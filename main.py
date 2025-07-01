from fastapi import FastAPI, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- CONFIG ---------- #
SHEET_NAME = "Breakdown Log"
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = "cosmic-adapter-444413-b1-207d1431f96b.json"
# ---------------------------- #

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPES)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

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
    try:
        sheet = get_sheet()
        row = [
            entry.equipment,
            entry.failure_description,
            entry.reported_by,
            entry.date_reported,
            entry.root_cause,
            entry.corrective_action,
            entry.resolved_by,
            entry.date_resolved
        ]
        sheet.append_row(row)
        print("✅ Breakdown logged to Google Sheet:", row)
        return {"message": "Breakdown logged to Google Sheet."}
    except Exception as e:
        print("❌ Failed to save breakdown:", e)
        return {"message": f"Error saving breakdown: {e}"}

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
        sheet = get_sheet()
        rows = sheet.get_all_values()

        if len(rows) < 2:
            return HTMLResponse("<h1>No breakdowns logged yet.</h1>")

        headers = rows[0]
        data_rows = rows[1:]

        query = dict(request.query_params)
        if "equipment" in query:
            data_rows = [r for r in data_rows if r[0] == query["equipment"]]
        if "reported_by" in query:
            data_rows = [r for r in data_rows if r[2] == query["reported_by"]]

        table = "<table border='1' cellpadding='5' style='border-collapse: collapse;'>"
        table += "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>"
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
            <h1>Breakdown History (Google Sheets)</h1>
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


