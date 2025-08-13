from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional
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
    SHEETS_WEBAPP_URL = os.getenv("SHEETS_WEBAPP_URL", "https://script.google.com/macros/s/AKfycbyp2RXahUVgZW9xMJyVYdCuyOcBoVqfpN_XeOQF91s8GjryvAakoCB2FdqVvlQ9Vtd2/exec")
    GOOGLE_SHEETS_SHARED_TOKEN = os.getenv("GOOGLE_SHEETS_SHARED_TOKEN", "your_shared_token_here")

    if not GOOGLE_SHEETS_SHARED_TOKEN or GOOGLE_SHEETS_SHARED_TOKEN == "your_shared_token_here":
        return {"status": "error", "message": "Missing GOOGLE_SHEETS_SHARED_TOKEN in environment"}

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

@app.get("/sheet/data", operation_id="get_sheet_data")
def get_sheet_data(
    auction_house: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    max_rows: Optional[int] = Query(50)
):
    SHEETS_WEBAPP_URL = os.getenv("SHEETS_WEBAPP_URL", "https://script.google.com/macros/s/AKfycbyp2RXahUVgZW9xMJyVYdCuyOcBoVqfpN_XeOQF91s8GjryvAakoCB2FdqVvlQ9Vtd2/exec")

    params = {
        "auction_house": auction_house,
        "start_date": start_date,
        "end_date": end_date,
        "max_rows": max_rows
    }

    response = requests.get(SHEETS_WEBAPP_URL, params=params)

    if not response.ok:
        return {"status": "error", "message": response.text}

    try:
        data = response.json()
    except Exception as e:
        return {"status": "error", "message": f"Invalid JSON: {e}"}

    return data