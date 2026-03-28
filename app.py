import os
import json
import sqlite3
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

app = FastAPI(title="Medical Search Relevancy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_FILE = "data.json"
DB_FILE = "feedback.db"

# Load realistic clinical dataset
with open(DATA_FILE, "r") as f:
    documents = json.load(f)

# Initialize feedback database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT,
            document_id TEXT,
            rating TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/search")
def search(q: str = ""):
    if not q:
        return {"results": []}
    
    q_lower = q.lower()
    
    # Intentionally naive keyword search for the relevancy exercise
    # Shows why keywords fail on negation ("no signs of diabetes")
    results = [doc for doc in documents if q_lower in doc["text"].lower()]
    return {"results": results}

@app.post("/feedback")
async def feedback(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})
        
    query = data.get("query")
    document_id = data.get("document_id")
    rating = data.get("rating")  # Expecting 'up' or 'down'
    
    if not query or not document_id or not rating:
        return JSONResponse(status_code=400, content={"error": "Missing fields"})
        
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO feedback (query, document_id, rating) VALUES (?, ?, ?)", 
              (query, document_id, rating))
    conn.commit()
    conn.close()
    
    return {"status": "success"}

# Serve the beautifully designed frontend
@app.get("/", response_class=HTMLResponse)
def read_root():
    if os.path.exists("index.html"):
        with open("index.html", "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>index.html not found! Please create it for the beautiful frontend.</h1>", status_code=404)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
