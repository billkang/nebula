## ADDED Requirements

### Requirement: Log reporting API endpoint
The system SHALL provide a `POST /api/v1/logs` endpoint that accepts frontend log entries and writes them to the backend log file.

#### Scenario: Log entry submitted
- **WHEN** a POST request is sent to `/api/v1/logs` with a valid JSON body containing `level`, `message`, `timestamp`, and optional `stack`
- **THEN** the backend SHALL write the entry to the log file at the corresponding log level
- **AND** return HTTP 200 with `{"data": {"accepted": true}}`

#### Scenario: Multiple log entries in one request
- **WHEN** a POST request is sent to `/api/v1/logs` with a JSON array of log entries
- **THEN** all entries SHALL be written to the log file
- **AND** return HTTP 200

### Requirement: JWT authentication for log reporting
The `POST /api/v1/logs` endpoint SHALL require JWT authentication, reusing the existing `get_current_user` dependency.

#### Scenario: Authenticated request succeeds
- **WHEN** a POST request includes a valid JWT token in the `Authorization` header
- **THEN** the endpoint SHALL accept and process the log entries

#### Scenario: Unauthenticated request rejected
- **WHEN** a POST request does not include a valid JWT token
- **THEN** the endpoint SHALL return HTTP 401 Unauthorized

### Requirement: Log entry validation
The endpoint SHALL validate incoming log entries. Invalid entries SHALL be logged as warnings on the server side but SHALL NOT cause the entire batch to be rejected (best-effort).

#### Scenario: Invalid log entry skipped
- **WHEN** a batch contains both valid and invalid log entries
- **THEN** the valid entries SHALL be written to the log file
- **AND** invalid entries SHALL be logged as server-side warnings
- **AND** the endpoint SHALL return HTTP 200

### Requirement: Frontend log batching
The frontend logger SHALL batch log entries and send them periodically (every 5 seconds or every 10 entries, whichever comes first) to reduce network overhead.

#### Scenario: Logs batched and sent
- **WHEN** 10 or more log entries are queued
- **THEN** the frontend SHALL immediately send the batch to the backend

#### Scenario: Periodic batch flush
- **WHEN** at least 1 log entry exists and 5 seconds have passed since the last send
- **THEN** the frontend SHALL flush the batch to the backend
