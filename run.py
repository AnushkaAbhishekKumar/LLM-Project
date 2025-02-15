# /// script
# requires-python = ">=3.11"
# dependencies = [
#        "fastapi",
#        "uvicorn",
#        "requests",
# ]
# ///
#
import uvicorn 
import os
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
import json
import os
from  subprocess import run 


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST"],  
    allow_headers=["*"],
)
# Ensure the OpenAI API key is set
#AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]
#if not AIPROXY_TOKEN:
    #raise RuntimeError("AIPROXY_TOKEN environment variable not set")

AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]



@app.get("/")
def home():
    return "working"     
          
            


@app.post("/run")
def run_task(task: str ):
    """Executes a task based on user input."""
    url= "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
}
    data= {
     "model":"gpt-4o-mini",
            "messages":[{"role": "user", "content": task},
                        {"role": "system", "content": "You are a helpful assistant that executes tasks."},
                      ]
}
    try:
        response = requests.post(url, headers=headers,json=data)
        
        result = response.json()
        r = result
        result = r["choices"][0]["message"]["content"]
        #return {"status": "success", "output": result}
        return r
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Task error: {str(e)}")
"""
@app.get("/read")
def read_file(path: str = Query(..., description="Path to the file to read")):
    #""Returns the content of a specified file.""
    if not path.startswith("/data/"):
        raise HTTPException(status_code=403, detail="Access to this file is not allowed")
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
"""
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)