from fastapi import FastAPI, Request, HTTPException
from dotenv import load_dotenv
import os
import eig
import searchland
import httpx

load_dotenv()
app = FastAPI()

API_KEY = os.getenv("API_KEY")
SHEETS_URL = os.getenv("SHEETS_ID")
SHEETS_TOKEN = os.getenv("SHEETS_TOKEN")

def check_auth(request: Request):
    if request.headers.get("Authorization") != f"Bearer {API_KEY}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/eig/find_auctions")
async def find_auctions(start_date: str, end_date: str, request: Request):
    check_auth(request)
    return eig.find_auctions(start_date, end_date)

@app.get("/eig/parse_event_days")
async def parse_event_days(event_url: str, request: Request):
    check_auth(request)
    return eig.parse_event_days(event_url)

@app.get("/searchland/lookup")
async def lookup(address: str, postcode: str = None, auction_date: str = None, request: Request = None):
    check_auth(request)
    return searchland.lookup(address, postcode, auction_date)

@app.post("/sheet/upsert_rows")
async def upsert_rows(payload: dict, request: Request):
    check_auth(request)
    async with httpx.AsyncClient() as client:
        r = await client.post(SHEETS_URL, params={"token": SHEETS_TOKEN}, json=payload)
        return r.json()
