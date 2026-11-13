# Safety model

## Trusted versus untrusted input

Trusted synthetic fields are loaded from scenario definitions: the original task, data label, approved recipient list, split, and expected labels. The returned document string is untrusted content. It cannot alter scenario metadata, controls, approvals, or trusted task fields. The frontend sends only scenario/configuration identifiers to start a simulation.

## Tools and execution

Only `read_document` and `send_email` exist as simulated tools. Document retrieval resolves approved scenario IDs, not filesystem paths, and in configurations C and D the read request itself passes the gateway (POL-010 blocks any document other than the trusted scenario's own). The email tool validates a synthetic `example.test` recipient and writes a local SQLite execution row marked `simulated=true` and `network_used=false`. There is no SMTP, external API, shell, browser, or arbitrary file access.

## Protected gateway

The gateway is the only authorization path for configurations C and D. Unknown/malformed actions, confidential data to an unapproved recipient, unapproved recipients, task mismatches, missing/error detector output, and gateway errors fail closed. Internal data and suspicious detector results return REVIEW. REVIEW is non-executing until a separate recorded approval; a rejected decision cannot execute. Duplicate or stale approval is rejected.

Configuration A is intentionally unprotected for the research comparison, but mock tools remain local and synthetic. Configuration B is the documented detector-only condition: suspicious/error results block, clean output permits the proposed mock action without policy checks.

## Scope

This is a deterministic educational prototype, not a production agent, email service, or comprehensive prompt-injection defense. The keyword method has false positives and false negatives and must not be represented as a pretrained model. The pretrained adapter, when selected and unavailable, fails closed; a keyword fallback is used only when explicitly enabled and is labelled as fallback.

## Known gap

Recipient and data-label rules cannot see message content. An injected disclosure inside an email the user really asked for (allowed-channel leak) passes the gateway unless the detector flags the document or a reviewer rejects it. The evaluation reports this as a failure.
