from fastapi import FastAPI, Form, Request
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
        print("🔍 Looking for form.html at:", file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>form.html not found</h1>", status_code=404)

@app.get("/logs", response_class=HTMLResponse)
def view_logs(request: Request):
    print("🔥 /logs route hit")
    try:
        if not os.path.exists(DATA_FILE):
            return HTMLResponse("<h1>No breakdowns logged yet.</h1>")

        with open(DATA_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)

        if len(rows) < 2:
            return HTMLResponse("<h1>No breakdowns logged yet.</h1>")

        headers = rows[0]
        data_rows = rows[1:]

        # Filter data based on query params
        query = dict(request.query_params)
        if "equipment" in query:
            data_rows = [r for r in data_rows if r[0] == query["equipment"]]
        if "reported_by" in query:
            data_rows = [r for r in data_rows if r[2] == query["reported_by"]]

        table = "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
        table += "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>"
        table += "<tbody>"
        for row in data_rows:
            table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        table += "</tbody></table>"

        search_form = """
        <form method='get'>
            <label>Filter by Equipment:</label>
            <input type='text' name='equipment' placeholder='e.g. Kinetic' />
            <label>Filter by Reported By:</label>
            <input type='text' name='reported_by' placeholder='e.g. Ian Petrick' />
            <button type='submit'>Filter</button>
        </form>
        <hr />
        """

        html = f"""
        <html>
        <head><title>Breakdown Logs</title></head>
        <body>
            <h1>Breakdown History</h1>
            {search_form}
            {table}
        </body>
        </html>
        """
        return HTMLResponse(html)

    except Exception as e:
        return HTMLResponse(f"<h1>Error reading logs: {e}</h1>", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000, reload=False)
