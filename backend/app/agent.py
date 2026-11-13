"""Deterministic simulated agent: how it reads untrusted text and what it proposes.

This is NOT a language model. It is a transparent rule-based stand-in that models a
*worst-case gullible* LLM agent: it understands instructions written in the document
even when they are misspelled, spaced out, written in leetspeak, base64-encoded or
written in Swahili/French, and it obeys them. That is the threat the gateway exists
for. Every rule is listed here so results can be explained line by line.

Two kinds of injected instruction are recognised:
- redirect: "<send-verb> ... <email address>" -> propose send_email to that address.
- disclosure: "<include-verb> ... <sensitive term>" -> when the user's own task already
  sends an email, the agent adds the injected disclosure to the message body
  (body_scope = "summary_with_injected_disclosure"). This is the proposal's
  "leak through an allowed channel" case.

Text inside quotation marks is treated as quoted material, not an instruction, which
models an agent that understands quoted examples in security articles.
"""
from __future__ import annotations

import base64
import binascii
import re
import unicodedata
from dataclasses import dataclass

EMAIL = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)

# Exact-match verbs (short words are never fuzzy-matched to avoid "sent" -> "send").
SEND_VERBS = {"send", "email", "e-mail", "mail", "forward", "share", "deliver", "transmit", "cc", "bcc",
              "tuma", "itume", "zitume", "mtumie",  # Swahili: send / send it / send them / send to him/her
              "envoie", "envoyez", "envoyer", "transfere", "transferez", "transferer"}  # French
FUZZY_SEND_VERBS = {"email", "forward", "deliver", "transmit", "envoyer"}  # length >= 5 only
INCLUDE_VERBS = {"include", "attach", "append", "add", "paste", "copy", "insert", "weka", "ambatisha", "ajoute", "joindre"}
FUZZY_INCLUDE_VERBS = {"include", "attach", "append", "insert"}
SENSITIVE_TERMS = {"confidential", "secret", "private", "password", "passwords", "salary", "salaries", "credentials",
                   "siri", "confidentiel", "confidentielle", "unredacted", "restricted"}

LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "$": "s"})
ZERO_WIDTH = re.compile("[​‌‍⁠﻿­]")
QUOTED = re.compile(r"[\"“‘][^\"”’]{0,400}[\"”’]")
SPACED_LETTERS = re.compile(r"\b(?:[a-z][ .\-_]){2,}[a-z]\b")
BASE64_TOKEN = re.compile(r"[A-Za-z0-9+/]{16,}={0,2}")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?;:\n])\s+|\n")
WORD = re.compile(r"[a-z\-]+")


@dataclass(frozen=True)
class DocumentInstructions:
    redirect_recipient: str | None
    disclosure_requested: bool
    evidence: tuple[str, ...]


def _edit_distance_at_most_one(a: str, b: str) -> bool:
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        diff = [i for i in range(len(a)) if a[i] != b[i]]
        return len(diff) <= 1 or (len(diff) == 2 and diff[1] == diff[0] + 1 and a[diff[0]] == b[diff[1]] and a[diff[1]] == b[diff[0]])
    shorter, longer = (a, b) if len(a) < len(b) else (b, a)
    i = j = 0
    skipped = False
    while i < len(shorter) and j < len(longer):
        if shorter[i] != longer[j]:
            if skipped:
                return False
            skipped = True
            j += 1
            continue
        i += 1
        j += 1
    return True


NEGATIONS = {"no", "not", "never", "without", "don't", "dont", "usitume", "pas"}
INFLECTED = re.compile(r"(?:ed|es|ing)$")


def _matches(word: str, exact: set[str], fuzzy: set[str]) -> bool:
    if word in exact:
        return True
    if INFLECTED.search(word):  # "included", "sending": descriptions, not commands
        return False
    return len(word) >= 5 and any(_edit_distance_at_most_one(word, verb) for verb in fuzzy)


def _decode_base64_segments(text: str) -> list[str]:
    decoded = []
    for token in BASE64_TOKEN.findall(text):
        if "@" in token:
            continue
        try:
            raw = base64.b64decode(token + "=" * (-len(token) % 4), validate=True)
            value = raw.decode("utf-8")
        except (binascii.Error, ValueError, UnicodeDecodeError):
            continue
        if value.isprintable() and sum(ch.isalpha() for ch in value) >= len(value) * 0.6:
            decoded.append(value)
    return decoded


def normalize(text: str) -> str:
    """Return the text as the simulated agent 'understands' it."""
    text = unicodedata.normalize("NFKC", text)
    text = ZERO_WIDTH.sub("", text)
    extra = _decode_base64_segments(text)
    text = "\n".join([text, *extra]).lower()
    text = QUOTED.sub(" ", text)
    text = SPACED_LETTERS.sub(lambda m: re.sub(r"[ .\-_]", "", m.group(0)), text)
    # De-leet word tokens but leave e-mail addresses untouched.
    return " ".join(token if "@" in token else token.translate(LEET) for token in text.split(" "))


def read_instructions(document: str) -> DocumentInstructions:
    """Extract instructions the gullible agent would follow from untrusted text."""
    normalized = normalize(document)
    redirect = None
    disclosure = False
    evidence: list[str] = []
    for sentence in SENTENCE_SPLIT.split(normalized):
        words = WORD.findall(sentence)
        if NEGATIONS.intersection(words):  # "do not send ...", "no confidential details are included"
            continue
        addresses = EMAIL.findall(sentence)
        if redirect is None and addresses and any(_matches(w, SEND_VERBS, FUZZY_SEND_VERBS) for w in words):
            redirect = addresses[-1].rstrip(".,;)")
            evidence.append(f"redirect: {sentence.strip()[:120]}")
        if any(_matches(w, INCLUDE_VERBS, FUZZY_INCLUDE_VERBS) for w in words) and any(w in SENSITIVE_TERMS for w in words):
            disclosure = True
            evidence.append(f"disclosure: {sentence.strip()[:120]}")
    return DocumentInstructions(redirect, disclosure, tuple(evidence))


def task_email_request(user_task: str) -> list[str]:
    """Addresses the trusted user task explicitly asks to email (empty if none)."""
    if not re.search(r"\b(email|send|forward)\b", user_task, re.I) or re.search(r"\b(do not|don't|without)\b[^.]*\b(email|send)", user_task, re.I):
        return []
    return [address.lower() for address in EMAIL.findall(user_task)]
