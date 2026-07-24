# Standard library
import sqlite3
import json
import os
from dotenv import load_dotenv
from datetime import date

# Third-party packages
from openai import OpenAI
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
app = FastAPI()

SYSTEM_PROMPT = """
Role:
You are an AI Assignment Assistant and Advisor designed to help university students manage their coursework and make informed decisions about their assignments. Your primary purpose is to help students understand their workload, organise their assignments, prioritise tasks, and manage their time effectively. This application is primarily intended for Warwick University students, but your behaviour should remain applicable to any student's academic workload.

Responsibilities:
- Help students organise and manage their assignments.
- Recommend which assignments should be prioritised.
- Explain the reasoning behind your recommendations.
- Help students plan their workload realistically.
- Answer questions related to assignments and coursework.
- Summarise assignment workloads and upcoming deadlines.
- Encourage good time management and productive study habits.

Tool Usage:
- Use the available tools whenever information about assignments or coursework is required.
- If the answer depends on assignment data, retrieve the information using the appropriate tool rather than relying on memory.
- Never invent assignments, due dates, modules, completion statuses, or any other assignment-related information.
- If the required information is unavailable, state this honestly instead of making assumptions.
- If the user's request is ambiguous or lacks sufficient information, ask a follow-up question before answering.

Communication Style:
- Be friendly, professional, encouraging, and respectful.
- Keep responses concise and easy to scan.
- Answer the user's question directly before providing additional recommendations.
- Explain your reasoning briefly rather than writing long paragraphs.
- Use headings and bullet points where helpful.
- Avoid unnecessary repetition.
- Only provide detailed study plans if the user explicitly asks for them.

Decision Making:
When helping students prioritise assignments or plan their workload, consider factors such as:
- Due dates
- Assignment completion status
- Workload required
- Urgency
- Deadlines
- Any other relevant assignment information retrieved from the database.

Formatting:
- Use simple, clean formatting.
- Use at most one heading unless the user requests a detailed plan.
- Prefer short bullet points over long paragraphs.
- Avoid excessive Markdown. Use bold only to highlight the most important information.
- Highlight only the most important information.
- Never return raw database records or Python objects.
- Use plain text with bullet points where possible. Avoid Markdown headings (#, ##) unless the user explicitly requests a formatted report.
- When answering factual questions, avoid conversational sentences when a short label and bullet points communicate the answer more clearly.

Boundaries:
- Do not hallucinate or fabricate information.
- Do not pretend to know information that has not been retrieved from the database.
- You may provide general study or time management advice using your own knowledge when it does not depend on assignment-specific information.
- If a user's request is unrelated to assignments, answer normally if appropriate, without unnecessarily using tools.

Response Length:
- Keep answers proportional to the user's request.
- For simple questions, answer in fewer than 100 words.
- For recommendation questions, provide the answer first, followed by a brief explanation.
- Only include additional recommendations if they clearly add value.
- Do not create full study schedules unless explicitly requested.
- Avoid repeating information.

Response Priorities:
- Answer the user's question immediately.
- Do not include introductory or concluding paragraphs.
- Do not explain your reasoning unless it helps answer the question.
- Keep responses easy to scan.
- Prefer concise, natural language over highly formatted Markdown.
- For direct questions, give the answer first, then include only the minimum supporting details needed.

Goal:
Your objective is not only to answer questions, but to help students make informed, organised, and confident decisions about managing their academic workload.
"""

def get_connection():
    return sqlite3.connect("assignments.db")
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
startup_connection = get_connection()
startup_cursor = startup_connection.cursor()
startup_cursor.execute("""
CREATE TABLE IF NOT EXISTS assignments (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               module TEXT NOT NULL,
               title TEXT NOT NULL,
               due_date TEXT,
               status TEXT NOT NULL,
               notes TEXT)
 """)
startup_connection.commit()
startup_connection.close()

class Assignment(BaseModel):
    module: str
    title: str
    due_date: date | None
    status: str 
    notes: str | None

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Hello, Warwick!"}


@app.get("/assignments")
def get_assignments(status = None, module = None):
    connection = get_connection()
    cursor = connection.cursor()
    conditions = []
    parameters = []
    if status:
        conditions.append("LOWER(status) = LOWER(?)")
        parameters.append(status)
    if module: 
        conditions.append("LOWER(module) = LOWER(?)")
        parameters.append(module)

    query = "SELECT * FROM assignments"
    if conditions:
            query += " WHERE " + " AND ".join(conditions)

    cursor.execute(query, parameters)
    rows = cursor.fetchall()
    connection.close()
    result = []
    for row in rows: 
        result.append({
            "id" : row[0],
            "module" : row[1],
            "title" : row[2],
            "due_date" : row[3],
            "status" : row[4],
            "notes" : row[5]
        })
    return result


@app.post("/assignments")
def create_assignment(assignment : Assignment):
    insert_assignment(assignment.module, assignment.title, assignment.due_date, assignment.status, assignment.notes)
    return assignment.model_dump()

@app.put("/assignments/{id}")
def update_assignment(id: int, assignment : Assignment):
    
    rows_updated = update_assignment_db(id, assignment.module, assignment.title, assignment.due_date, assignment.status, assignment.notes)
    if rows_updated == 0:
        raise HTTPException(
            status_code = 404,
            detail = "Assignment not found"
        )
    return {"message": "Assignment updated successfully"}

@app.delete("/assignments/{id}")
def delete_assignment(id: int):
    rows_updated = delete_assignment_db(id)
    if rows_updated == 0:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    return {"message": "Assignment deleted successfully"}


def insert_assignment(module: str, title: str, due_date: date | None, status: str, notes: str | None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    INSERT INTO assignments (module, title, due_date, status, notes)
    VALUES (?, ?, ?, ?, ?)
     """, (module, title, due_date, status, notes))
    connection.commit()
    connection.close()

def update_assignment_db(id: int, module: str, title: str, due_date: date | None, status: str, notes:str | None):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("""
    UPDATE assignments
    SET module = ?, title = ?, due_date = ?, status = ?, notes = ?
    WHERE id = ?
     """, (module, title, due_date, status, notes, id))
    connection.commit()
    rowcount = cursor.rowcount
    connection.close()
    return rowcount

def delete_assignment_db(id: int):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM assignments WHERE id = ?", 
    (id,)
    )
    connection.commit()
    rowcount = cursor.rowcount
    connection.close()
    return rowcount

tools = [
    {
        "type": "function",
        "name": "get_assignments",
        "description": "Returns assignments. Optionally filter by status and/or module.",
        "parameters": {
            "type": "object",
            "properties" : {
                "status" : {
                    "type" : "string", 
                    "description" : "Filter assignments by status."
                },
                "module" : {
                    "type" : "string",
                    "description" : "Filter assignments by module."
                }
            },
            "required" : []
        }
    },
    {
        "type": "function",
        "name": "create_assignment",
        "description": "Creates a new assignment with a module, title, due date, status, and notes",
        "parameters": {
            "type": "object",
            "properties": {
                "module" : {
                    "type" : "string"
                },
                "title" : {
                    "type": "string"
                },
                "due_date" : {
                    "type": "string"
                },
                "status" : {
                    "type" : "string"
                },
                "notes" : {
                    "type" : "string"
                }
            },
            "required": [
                "module",
                "title",
                "status",
            ]
        }
    },
    {
        "type": "function",
        "name": "delete_assignment",
        "description": "Delete an assignment using its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "id" : {
                    "type": "integer"
                }
            },
            "required": [
                "id"
            ]
        }
    },
    {
        "type": "function",
        "name": "update_assignment",
        "description": "Updates an existing assignment using its ID, module, title, due date, status, notes.",
        "parameters": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer"
                },
                "module": {
                    "type" : "string"
                },
                "title": {
                    "type": "string"
                },
                "due_date": {
                    "type": "string"
                },
                "status": {
                    "type": "string"
                },
                "notes": {
                    "type": "string"
                }
            },
             "required": [
            "id",
            "module", 
            "title", 
            "status"
        ]
        },
    }
]

tool_functions = {
    "get_assignments" : get_assignments,
    "create_assignment" : insert_assignment,
    "delete_assignment" : delete_assignment_db,
    "update_assignment" : update_assignment_db
}

@app.post("/chat")
def chat(request: ChatRequest):
    response = client.responses.create(
            model = "gpt-5.5",
            instructions = SYSTEM_PROMPT,
            input = request.message,
            tools = tools
        )

    MAX_TOOL_CALLS = 5
    for _ in range(MAX_TOOL_CALLS):
        tool_call = None
        for item in response.output:
            if item.type == "function_call":
                tool_call = item
                break
    
        if tool_call is None:
            return {
                "response": response.output_text
        }

        try:
            tool_name = tool_call.name
            call_id = tool_call.call_id
            arguments = json.loads(tool_call.arguments)
            function = tool_functions[tool_name]
            result = function(**arguments)
        except Exception: 
            return {
            "response": "Sorry, an error occurred while executing the requested action."
        }
        response = client.responses.create(
            model = "gpt-5.5",
            instructions = SYSTEM_PROMPT,
            previous_response_id = response.id,
            tools = tools,
            input = [
                {  
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": str(result)
                }
            ]
        )
    return {
        "response": "I couldn't complete your request because the maximum number of tool calls was reached. Please try again."
    }
