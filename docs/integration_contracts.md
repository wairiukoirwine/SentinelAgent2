# Integration contracts

## REST requests

- `POST /api/simulate`: `{ "scenario_id": "...", "configuration_id": "baseline|content_only|gateway_only|combined" }`. Trusted scenario policy fields are loaded server-side.
- `POST /api/approvals/{action_id}`: `{ "approved": true|false, "reviewer": "Local simulated reviewer" }`. Approval is separate from the initial simulation request.
- `POST /api/experiments/run`: `{ "configuration_ids": [...], "splits": [...], "scenario_ids": null|[...] }`.

## Responses and errors

Detector and gateway result schemas are described in `data_dictionary.md`. HTTP 404 identifies unknown scenario/action/experiment; HTTP 409 identifies a stale/duplicate review decision; validation failures use 422. Internal stack traces are not returned. Detector/gateway exceptions are converted into explicit fail-closed result records for protected execution.

## Audit event names

The implementation records `simulation_started`, `document_read_requested`, `document_read_completed`, `detector_evaluated` or `detector_failed`, `action_proposed`, `gateway_evaluated` or `gateway_failed`, `approval_requested`, `approval_recorded`, `mock_execution_attempted`, `mock_execution_completed`, and `simulation_completed` when applicable.

The API schema is also available through FastAPI OpenAPI at `/openapi.json` and Swagger UI at `/docs`.
