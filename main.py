from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from openai import OpenAI
import json
import os

app = FastAPI()

connection = sqlite3.connect(
    "assignments.db",
    check_same_thread=False
)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
cursor = connection.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS assignments (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               module TEXT,
               title TEXT,
               completed BOOLEAN)
 """)
connection.commit()

class Assignment(BaseModel):
    module: str
    title: str
    completed: bool

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"message": "Hello, Warwick!"}


@app.get("/assignments")
def get_assignments():
    cursor.execute("SELECT * FROM assignments")
    rows = cursor.fetchall()
    result = []
    for row in rows: 
        result.append({
            "id" : row[0],
            "module" : row[1],
            "title" : row[2],
            "completed" : bool(row[3])
        })
    return result


@app.post("/assignments")
def create_assignment(assignment : Assignment):
    insert_assignment(assignment.module, assignment.title, assignment.completed)
    return assignment.model_dump()

@app.put("/assignments/{id}")
def update_assignment(id: int, assignment : Assignment):
    
    update_assignment_db(id, assignment.module, assignment.title, assignment.completed)
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code = 404,
            detail = "Assignment not found"
        )
    return {"message": "Assignment updated successfully"}

@app.delete("/assignments/{id}")
def delete_assignment(id: int):
    delete_assignment_db(id)
    if cursor.rowcount == 0:
        raise HTTPException(
            status_code=404,
            detail="Assignment not found"
        )

    return {"message": "Assignment deleted successfully"}

def fetch_assignments():
    cursor.execute("SELECT * FROM assignments")
    rows = cursor.fetchall()
    return rows

def insert_assignment(module: str, title: str, completed: bool):
    cursor.execute("""
    INSERT INTO assignments (module, title, completed)
    VALUES (?, ?, ?)
     """, (module, title, completed))
    connection.commit()

def update_assignment_db(id: int, module: str, title: str, completed: bool):
    cursor.execute("""
    UPDATE assignments
    SET module = ?, title = ?, completed = ?
    WHERE id = ?
     """, (module, title, completed, id))
    
    connection.commit()

def delete_assignment_db(id: int):
    cursor.execute("DELETE FROM assignments WHERE id = ?", 
    (id,)
    )
    connection.commit()
    

tools = [
    {
        "type": "function",
        "name": "get_assignments",
        "description": "Returns all assignments from the SQLite database including module, title, and completion status. Use this whenever the user asks about assignments. ",
        "parameters": {
            "type": "object",
            "properties" : {},
            "required" : []
        }
    },
    {
        "type": "function",
        "name": "create_assignment",
        "description": "Creates a new assignment with a module, title, and completion status.",
        "parameters": {
            "type": "object",
            "properties": {
                "module" : {
                    "type" : "string"
                },
                "title" : {
                    "type": "string"
                },
                "completed" : {
                    "type": "boolean"
                }
            },
            "required": [
                "module",
                "title",
                "completed"
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
        "description": "Updates an existing assignment using its ID, module, title, and completion status.",
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
                "completed" : {
                    "type": "boolean"
                }
            },
             "required": [
            "id",
            "module", 
            "title", 
            "completed"
        ]
        },
    }
]

tool_functions = {
    "get_assignments" : fetch_assignments,
    "create_assignment" : insert_assignment,
    "delete_assignment" : delete_assignment_db,
    "update_assignment" : update_assignment_db
}

@app.post("/chat")
def chat(request: ChatRequest):
    response = client.responses.create(
            model = "gpt-5.5",
            input = request.message,
            tools = tools
        )
        
    print(response)

    while True:
        tool_call = None
        for item in response.output:
            if item.type == "function_call":
                tool_call = item
                break
    
        if tool_call is None:
            return {
                "response": response.output_text=[]
        }

        tool_name = tool_call.name
        call_id = tool_call.call_id
        arguments = json.loads(tool_call.arguments)
        function = tool_functions[tool_name]
        print(arguments)
        result = function(**arguments)
        response = client.responses.create(
            model = "gpt-5.5",
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
        print("\nAfter tool output:\n")
        print(response)

        continue
