from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ---------- CONFIG ---------- #
SHEET_NAME = "Breakdown Log"
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = "cosmic-adapter-444413-b1-207d1431f96b.json"
# ---------------------------- #

app = FastAPI()

# CORS for HTML frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Google Sheets access
def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPES)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# Breakdown model
class Breakdown(BaseModel):
    equipment: str
    failure_description: str
    reported_by: str
    date_reported: str
    root_cause: Optional[str] = ""
    corrective_action: Optional[str] = ""
    resolved_by: Optional[str] = ""
    date_resolved: Optional[str] = ""

# POST new breakdown to Google Sheets
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
        print("✅ Logged:", row)
        return {"message": "Breakdown logged to Google Sheet."}
    except Exception as e:
        print("❌ Logging failed:", e)
        return {"error": str(e)}

# Serve HTML form
@app.get("/form", response_class=HTMLResponse)
def breakdown_form():
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        form_path = os.path.join(base_path, "form.html")
        with open(form_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>form.html not found</h1>", status_code=404)

# Logs view
@app.get("/logs", response_class=HTMLResponse)
def view_logs(request: Request):
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

        table = "<table border='1' cellpadding='5'><thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead><tbody>"
        for row in data_rows:
            table += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        table += "</tbody></table>"

        filters = """
        <form method='get'>
            <label>Filter by Equipment:</label>
            <input type='text' name='equipment' />
            <label>Filter by Reported By:</label>
            <input type='text' name='reported_by' />
            <button type='submit'>Filter</button>
        </form><hr />
        """

        return HTMLResponse(f"<html><body><h1>Breakdown Logs</h1>{filters}{table}</body></html>")
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading logs: {e}</h1>", status_code=500)

# Only needed for local testing (ignored on Render)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)



