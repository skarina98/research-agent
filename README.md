# Research Agent API

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install
cp .env.example .env
uvicorn main:app --port 8080
```
