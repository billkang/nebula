## ADDED Requirements

### Requirement: Frontend logger utility
The frontend SHALL provide a `logger` utility module with `info()`, `warn()`, and `error()` methods. Each method SHALL output to the browser console with a `[Nebula]` prefix and SHALL also send the log entry to the backend for persistence.

#### Scenario: Logger writes to console
- **WHEN** `logger.info('User logged in')` is called in browser code
- **THEN** `[Nebula] User logged in` SHALL appear in the browser DevTools console
- **AND** the same entry SHALL be queued for backend reporting

#### Scenario: Logger error includes stack trace
- **WHEN** `logger.error('Something failed', error)` is called with an Error object
- **THEN** the console output SHALL include the error's message and stack trace

#### Scenario: Logger silently degrades when backend unreachable
- **WHEN** the backend log reporting endpoint is unreachable (e.g., backend not running)
- **THEN** the frontend SHALL NOT throw an error or show any UI alert
- **AND** log entries SHALL continue to appear in the browser console
- **AND** the queued entries SHALL be automatically retried on the next flush cycle

#### Scenario: Logger warn suppresses non-error reporting
- **WHEN** `logger.warn('Deprecated API used')` is called
- **THEN** the message SHALL appear in the console
- **AND** the entry SHALL be sent to the backend for persistence

### Requirement: API client logging
The API client (`client.ts`) SHALL log every outgoing request and its response at appropriate levels.

#### Scenario: Successful API call logged
- **WHEN** the API client sends a request and receives a 2xx response
- **THEN** a log entry SHALL be written with method, URL path, and response status code at INFO level

#### Scenario: Failed API call logged
- **WHEN** the API client receives a 4xx or 5xx response
- **THEN** the error SHALL be logged at ERROR level with status code, response body, and error details

#### Scenario: Network error logged
- **WHEN** the API client fails due to a network error (no response received)
- **THEN** the error SHALL be logged at ERROR level with the error message

### Requirement: Global Error Boundary
The frontend SHALL include a React Error Boundary component that wraps the application. It SHALL catch unhandled rendering errors, log them via the logger utility, and display a fallback UI.

#### Scenario: Error caught by boundary
- **WHEN** a React component throws an error during rendering
- **THEN** the Error Boundary SHALL catch the error
- **AND** call `logger.error()` with the error details
- **AND** display a fallback UI with a "Something went wrong" message and a "Reload" button

#### Scenario: Error boundary does not affect normal rendering
- **WHEN** no error occurs during React rendering
- **THEN** the Error Boundary SHALL render its children normally without any visible impact

### Requirement: Page close log flush
When the user closes or navigates away from the page, any queued but unsent log entries SHALL be flushed to the backend using `navigator.sendBeacon()`.

#### Scenario: Logs flushed on page close
- **WHEN** the user closes the browser tab or navigates to a different page
- **THEN** any remaining queued log entries SHALL be sent to the backend via `navigator.sendBeacon()`
