from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import csv
import os

app = FastAPI()

# Enable access from local HTML page
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "data/breakdowns.csv"

# Ensure data folder exists
os.makedirs("data", exist_ok=True)

# Define data model
class Breakdown(BaseModel):
    equipment: str
    failure_description: str
    reported_by: str
    date_reported: str
    root_cause: Optional[str] = ""
    corrective_action: Optional[str] = ""
    resolved_by: Optional[str] = ""
    date_resolved: Optional[str] = ""

@app.post("/breakdown")
def log_breakdown(entry: Breakdown):
    write_mode = 'a' if os.path.exists(DATA_FILE) else 'w'
    with open(DATA_FILE, write_mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_mode == 'w':
            writer.writerow(entry.dict().keys())  # Header row
        writer.writerow(entry.dict().values())
    return {"message": "Breakdown logged successfully."}

@app.get("/form", response_class=HTMLResponse)
def breakdown_form():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, "form.html")
        print("🔍 Looking for form.html at:", file_path)  # Debug print
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>form.html not found</h1>", status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)