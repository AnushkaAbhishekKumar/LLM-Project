# /// script
# requires-python = ">=3.11"
# dependencies = [
#        "fastapi",
#        "uvicorn",
#        "requests",
#         "httpx",
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
from subprocess import run

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["GET", "POST"],  
    allow_headers=["*"],
)
# Ensure the OpenAI API key is set
AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]
#if not AIPROXY_TOKEN:
    #raise RuntimeError("AIPROXY_TOKEN environment variable not set")AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]

@app.get("/")
def home():
    return "working"     
          
  # Pydantic Model for /run API Request
class TaskRequest(BaseModel):
    task: str
          
"""
@app.post("/run")
def run_task(task: str ):
    ""#Executes a task based on user input.""
    url= "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
}
    prompt = f"Generate a bash command or Python script to perform the following task: {task}. Only return the command or script and if python dependencies needed store in a json body, no explanations"

    data= {
     "model":"gpt-4o-mini",
            "messages":[{"role": "user", "content": task},
                        {"role": "system", "content":prompt },
                      ]
}
    try:
        response = requests.post(url, headers=headers,json=data)
        
        result = response.json()
        r = result["choices"][0]["message"]["content"]
        #return {"status": "success", "output": result}
        
        return r
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Task error: {str(e)}")
"""    

@app.post("/run")
def run_task(task: str):
    """Fetch execution command from LLM but DO NOT execute it here."""
    
    url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    prompt = f"""
    You are an automated execution agent running inside a Docker container.
    Your task is to generate a Python script or a Bash command to accomplish the given task.
    

    Assume uv is preinstalled. If the script needs to be executed with uv, use: uv run {{script_name}} {{arguments}}.
    If any Python dependencies are required, return them separately in a JSON format.

    Only output the command or script. Do not provide explanations, comments, or extra text.
    If any other description then up to you to run the task
    Now, generate the required command or script for the following task: {task}
    """

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AIPROXY_TOKEN}"
    }

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": task}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response_json = response.json()
        
        # Extract the execution command from LLM response
        execution_code = response_json["choices"][0]["message"]["content"]

        # Execute the extracted command separately
        result = execute_task(execution_code)

        return {"status": "success", "output": result, "response":response_json}
    

    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Task error: {str(e)}")




def execute_task(execution_code: str):
    """Executes the given bash or Python script."""
    print(f"Executing:\n{execution_code}")

    script_code = ""
    dependencies = {}
    script_name = "script.py"  # Default script name

    # Extract the Python script from the response
    parts = execution_code.split("```")
    for part in parts:
        if part.startswith("python"):
            script_code = part.split("\n", 1)[1]  # Extract script
        elif part.startswith("json"):
            try:
                dependencies = json.loads(part.split("\n", 1)[1])  # Extract dependencies
            except json.JSONDecodeError:
                dependencies = {}
        elif part.startswith("bash"):
            bash_command = part.split("\n", 1)[1].strip()
            if "uv run" in bash_command:
                script_name = bash_command.split("uv run")[-1].strip()

    # Ensure script_code is not empty
    if not script_code.strip():
        return {"error": "No valid script code received."}

    # Define script path correctly
    script_path = f"/tmp/{script_name}"

    try:
        # Save script to a file
        with open(script_path, "w") as script_file:
            script_file.write(script_code)

        # Ensure file is saved
        if not os.path.exists(script_path):
            return {"error": f"Failed to create script file: {script_path}"}

        # Ensure file is executable
        os.chmod(script_path, 0o755)

        # Execute the script using `uv run`
        result = run(["uv", "run", script_path], capture_output=True, text=True)

        # Cleanup script after execution
        os.remove(script_path)

        return {"stdout": result.stdout, "stderr": result.stderr}

    except Exception as e:
        return {"error": f"Execution failed: {str(e)}"}


def install_dependencies(dependencies):
    """Install required dependencies using uv."""
    if "dependencies" in dependencies:
        for package, version in dependencies["dependencies"].items():
            install_cmd = f"{package}" if version == "latest" else f"{package}=={version}"
            try:
                run(["uv", "pip", "install", install_cmd], check=True, text=True)
                print(f"Installed: {install_cmd}")
            except run.CalledProcessError as e:
                print(f"Error installing {install_cmd}: {e}")





def execute_with_retry(task: str, max_retries=2):
    for attempt in range(max_retries):
        result = execute_task(task)
        if not result["stderr"]:  # If no errors, return result
            return result
        print(f"Attempt {attempt + 1} failed: {result['stderr']}")
    
    return {"error": "Execution failed after retries"}                
@app.get("/read")

def read_file(path: str):
    """Returns the content of a specified file."""
    if not path.startswith("/data/"):
        raise HTTPException(status_code=403, detail="Access to this file is not allowed")
    
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        with open(path, "r") as file:
            content = file.read()
        return {"status": "success", "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
    
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)