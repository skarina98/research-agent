from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests
from eig import process_auctions_to_sheets

app = FastAPI()

# ----------------------------
# Existing EIG pipeline route
# ----------------------------

class RunEIGRequest(BaseModel):
    start_date: str
    end_date: str

@app.post("/eig/run_pipeline", operation_id="run_eig_pipeline")
def run_pipeline(req: RunEIGRequest):
    result = process_auctions_to_sheets(req.start_date, req.end_date)
    return result

# ----------------------------
# New Insight Posting Endpoint
# ----------------------------

class InsightPayload(BaseModel):
    auction_name: str
    auction_date: str
    lot_number: str
    insight: str

@app.post("/sheet/insights", operation_id="post_insights")
def post_insight(payload: InsightPayload):
    SHEETS_WEBAPP_URL = os.getenv("SHEETS_WEBAPP_URL")
    GOOGLE_SHEETS_SHARED_TOKEN = os.getenv("GOOGLE_SHEETS_SHARED_TOKEN")

    if not SHEETS_WEBAPP_URL or not GOOGLE_SHEETS_SHARED_TOKEN:
        return {"status": "error", "message": "Missing SHEETS_WEBAPP_URL or GOOGLE_SHEETS_SHARED_TOKEN in environment"}

    row = {
        "auction_name": payload.auction_name,
        "auction_date": payload.auction_date,
        "lot_number": payload.lot_number,
        "insight": payload.insight
    }

    response = requests.post(SHEETS_WEBAPP_URL, json={
        "token": GOOGLE_SHEETS_SHARED_TOKEN,
        "rows": [row]
    })

    if not response.ok:
        return {"status": "error", "message": response.text}

    return {"status": "success", "message": "Insight posted successfully"}
