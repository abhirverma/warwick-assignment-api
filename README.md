# AI Assignment Advisor API
## Overview
This project is an AI-powered Assignment Advisor that enables students to manage their coursework using natural language. Instead of manually navigating through menus or forms, users can simply ask questions such as "Show me my pending assignments" or "Create a study plan for my next three days", and the assistant determines the appropriate backend functions required to fulfil the request.

The application is built using **FastAPI**, **SQLite**, and the **OpenAI Responses API**. The backend combines traditional CRUD operations with OpenAI's tool calling capability, allowing the language model to intelligently select and execute backend functions before generating a final response. 

The system supports multiple tool calls when necessary, with a maximum of five iterations per request to prevent infinite loops while still allowing complex queries to be completed.

## Features
- Add new assignments.
- View all assignments.
- Update existing assignments.
- Delete assignments.
- Filter assignments by module.
-  Filter assignments by completion status.
-  Interact with the application using natural language.
-  Generate personalised study plans.
-  Prioritise assignments based on deadlines and completion status.
-  Persistent assignment storage using SQLite.
-  Dynamic backend function selection through OpenAI tool calling.

## Tech Stack
- **Python** – Primary programming language.
- **FastAPI** – REST API framework used to build the backend.
- **SQLite** – Lightweight relational database used for persistent assignment storage.
- **OpenAI Responses API** – Provides natural language understanding and tool calling capabilities.
- **Pydantic** – Validates incoming request data and ensures correct data types.
- **Uvicorn** – ASGI server used to run the FastAPI application.

## Architecture
The user sends a natural language request to the FastAPI backend through the /chat endpoint. The request is then passed to the OpenAI Responses API, where the language model determines whether any backend tools are required to answer the user's query.
If no backend function is needed, the model generates a response immediately. If tool execution is required, the model selects the appropriate backend CRUD function, which interacts with the SQLite database. The retrieved assignment data is then returned
to the OpenAI Responses API, allowing the model to incorporate the database results into a final natural language response. This process can repeat for multiple tool calls when necessary, with a maximum of five iterations before returning the final response to the user.

## Architecture Diagram
<img width="283" height="962" alt="Architecture Diagram drawio" src="https://github.com/user-attachments/assets/0aede39b-84fc-46a8-b4b6-ce8a2dd81b56" />

## Screenshots

### API Overview
<img width="1512" height="946" alt="Screenshot 2026-07-25 at 5 32 02 PM" src="https://github.com/user-attachments/assets/5b4338e9-2a44-4e4e-a7a4-936b89c2ad73" />
FastAPI automatically generates interactive API documentation using Swagger UI, exposing CRUD endpoints alongside the natural language /chat endpoint.

### Chat Endpoint
<img width="1512" height="951" alt="Screenshot 2026-07-25 at 5 33 48 PM" src="https://github.com/user-attachments/assets/f1add94d-0eac-4050-b0df-a519991f2f65" />
The /chat endpoint accepts natural language requests, allowing users to interact with the assignment manager conversationally.

### Example Chat Request
<img width="1508" height="936" alt="Screenshot 2026-07-25 at 5 43 02 PM" src="https://github.com/user-attachments/assets/999ec057-54d7-4d4f-9482-9ee4f7fd6ef4" />
Example of the /chat endpoint processing the request "Which assignment is due next?". The OpenAI Responses API selects the appropriate backend function, retrieves assignment data from SQLite, and generates a natural language response.

### SQLite Database
<img width="457" height="232" alt="El assignments" src="https://github.com/user-attachments/assets/330bf2bc-ccd8-4ed7-b087-7a59cca94f16" />

Assignment information is stored persistently in a SQLite database. The database stores details such as the module, title, due date, status, and notes for each assignment.

## Example Prompts
- *"Show me all my pending assignments."*
- *"Which assignment is due next?"*
- *"Which assignment should I prioritise?"*
- *"Mark my CS126 coursework as complete."*
- *"Show me all pending assignments for ST117."*
- *"Prepare a detailed study plan for the next three days."*
- *"I'm overwhelmed. What should I study for the next three hours?"*
- *"Show me everything due this week."*

## Design Decisions
### Why FastAPI?
FastAPI was chosen because it is specifically designed for building REST APIs. Since this project is itself an API, FastAPI was a natural fit. One of FastAPI's biggest advantages is that it automatically generates interactive API documentation using Swagger UI as soon as API endpoints are created, meaning there is no need to manually write documentation for testing the endpoints.
Another advantage is its integration with Pydantic, which validates incoming requests before they reach the application logic. It automatically checks for missing fields, incorrect data types, and invalid request formats, making the application more reliable. In addition, FastAPI is one of the fastest Python web frameworks available and provides clean, concise, and easy-to-read code.

### Why SQLite?
SQLite was chosen because it is lightweight and well suited to the scope of this project. Unlike larger database systems such as PostgreSQL or MySQL, SQLite stores all data in a single database file (assignments.db) and does not require a separate database server or complex setup.
It is extremely easy to configure while still providing persistent storage, meaning assignment information is retained even after the application closes. Since this project is intended as a student application rather than a large-scale production system with thousands of users, SQLite provides all the functionality required while keeping the project simple.

### Why OpenAI Tool Calling?
Instead of manually checking user prompts using conditions such as:
```python
if "delete" in prompt:
    delete_assignment()
```
the application uses OpenAI's tool calling capability. This allows the model to decide which backend function should be executed based on the user's natural language request.
This approach is significantly more flexible than manually parsing prompts, allowing the assistant to understand a wider variety of user requests while selecting the appropriate function automatically. It also supports multiple tool calls when a single function is insufficient to answer the user's query.

### Why a Stateless API?
The API is intentionally designed to be stateless, meaning every request is processed independently without storing previous conversation history. This keeps the backend simpler and easier to scale while reducing the need for session management or conversation storage.
For the scope of this project, providing sufficient context within a single request allows the model to answer effectively. If multi-turn conversations become a future requirement, session-based conversation memory could be added as an enhancement.

### Why Per-Request Database Connections?
Initially, the application shared a single global SQLite connection and cursor across the entire application. During development, this was refactored so that each request creates its own local database connection and cursor before executing queries.
This design prevents multiple requests from interfering with one another, avoids shared mutable state, and ensures database resources are released after each request.

## Limitations
This project is currently limited to a relatively small scope and was designed as a demonstration of integrating FastAPI, SQLite, and the OpenAI Responses API, rather than as a production-ready application.
- The API is intentionally stateless, meaning previous conversations are not stored between requests. As a result, if a user sends a follow-up message without providing sufficient context, the model may not be able to correctly interpret the request.
- The project uses SQLite, which is well suited to small-scale applications but is not intended for systems with thousands of users or millions of assignments.
- The backend is currently designed for a single user and does not support multiple users.
- The application does not currently include authentication or user accounts.
- The project is API-only and does not include a dedicated frontend interface.

## Future Improvements
Several enhancements could be added in future versions of the project, including:
- Add session-based conversation memory to support multi-turn interactions.
- Add user authentication and support for multiple users.
- Integrate with calendar applications to automatically schedule study sessions.
- Add email or notification reminders for upcoming assignment deadlines.
- Refactor database operations to use try/finally blocks or context managers, ensuring database connections are always closed even if exceptions occur.
- Improve tool execution error handling by allowing tool errors to be returned to the language model, enabling it to recover gracefully or explain failures instead of immediately terminating the request.

## Getting Started

### Prerequisites

Before running the project, ensure you have the following installed:

- Python 3.11 or later
- `pip`
- An OpenAI API key

---

### Installation

1. Clone the repository:

```bash
git clone https://github.com/abhirverma/warwick-assignment-api.git
```

2. Navigate to the project directory:

```bash
cd warwick-assignment-api
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

### Configure the OpenAI API Key

1. Create a `.env` file in the project directory.
2. Add your OpenAI API key:

```env
OPENAI_API_KEY=your_api_key_here
```

---

### Running the Application

Start the FastAPI development server:

```bash
uvicorn main:app --reload
```

The API will then be available at:

```text
http://127.0.0.1:8000
```
The SQLite database (assignments.db) is created automatically when the application is first run if it does not already exist.

---

### Interactive API Documentation

FastAPI automatically generates interactive API documentation using Swagger UI.

Open the following URL in your browser:

```text
http://127.0.0.1:8000/docs
```

From here, you can:

- Explore all available API endpoints.
- Execute requests directly from your browser.
- Test the application's functionality without writing any additional client code.

