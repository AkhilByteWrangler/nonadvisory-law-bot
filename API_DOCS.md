# API Documentation: Nonadvisory Law Bot

## Base URL
- Local: `http://localhost:8000`

## Endpoints

### POST `/ask`
- **Description:** Ask a legal question. Returns answer, discussion, resources, and timestamp.
- **Request Body:**
  ```json
  { "question": "string" }
  ```
- **Response:**
  ```json
  {
    "answer": "string",
    "disclaimer": "string",
    "discussion": [ ... ],
    "timestamp": 1719168000000
  }
  ```
- **Errors:** 500 Internal Server Error

### GET `/history`
- **Description:** Get conversation history.
- **Response:** Array of conversation objects.

### DELETE `/history`
- **Description:** Clear conversation history.
- **Response:** `{ "status": "success" }`

### POST `/feedback`
- **Description:** Send emoji feedback for a bot message.
- **Request Body:**
  ```json
  { "message": "string", "emoji": "string", "timestamp": 1719168000000 }
  ```
- **Response:**
  ```json
  { "reply": "string" }
  ```

### GET `/feedback`
- **Description:** Get actionable feedback suggestions.
- **Response:**
  ```json
  { "future_improvement_feedback": [ ... ] }
  ```

## OpenAPI Docs
- Interactive docs: `/docs`

## Error Codes
- 500: Internal server error (see error message)

