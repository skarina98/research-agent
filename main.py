from fastapi import FastAPI
from pydantic import BaseModel
from eig import process_auctions_to_sheets

app = FastAPI()

class RunEIGRequest(BaseModel):
    start_date: str
    end_date: str

@app.post("/eig/run_pipeline", operation_id="run_eig_pipeline")
def run_pipeline(req: RunEIGRequest):
    result = process_auctions_to_sheets(req.start_date, req.end_date)
    return result