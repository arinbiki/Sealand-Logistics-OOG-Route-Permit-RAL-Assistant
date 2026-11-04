"""
Deploy Sealand Logistics OOG Workflows to n8n Instance via Public API
"""

import os
import json
import urllib.request
import urllib.error

N8N_BASE_URL = os.environ.get("N8N_BASE_URL", "https://ubuntu.arindam818.cloud/api/v1")
N8N_API_KEY = os.environ.get(
    "N8N_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI5YjU2NzE0My02MGI4LTQxNTUtYmFiOS1mYjM2OTE3YjVlMjgiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNmFjMzA1YzAtMzllNi00NzAyLTgwYmItY2UwMWM5MWNjYjNmIiwiaWF0IjoxNzkxMjg3NDA5LCJleHAiOjE3OTY0Mjg4MDB9.sr2NtXAe2c6xiNRYjBxEJHMfcdES7Zla6bjH2pcW0QA"
)

def deploy_workflow(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        wf_data = json.load(f)
        
    name = wf_data.get("name")
    print(f"Deploying '{name}' from {os.path.basename(file_path)}...")
    
    # 1. Check if workflow already exists
    req_list = urllib.request.Request(
        f"{N8N_BASE_URL}/workflows",
        headers={"X-N8N-API-KEY": N8N_API_KEY, "Accept": "application/json"}
    )
    existing_id = None
    try:
        with urllib.request.urlopen(req_list) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for item in data.get("data", []):
                if item.get("name") == name:
                    existing_id = item.get("id")
                    break
    except Exception as e:
        print(f"Error querying workflows: {e}")
        return None
        
    payload = {
        "name": name,
        "nodes": wf_data.get("nodes", []),
        "connections": wf_data.get("connections", {}),
        "settings": wf_data.get("settings", {})
    }
    
    if existing_id:
        print(f"Workflow '{name}' already exists (ID: {existing_id}). Updating...")
        req_update = urllib.request.Request(
            f"{N8N_BASE_URL}/workflows/{existing_id}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
            method="PUT"
        )
        with urllib.request.urlopen(req_update) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"Successfully updated '{name}' (ID: {res.get('id', existing_id)})")
            return res
    else:
        print(f"Creating new workflow '{name}'...")
        req_create = urllib.request.Request(
            f"{N8N_BASE_URL}/workflows",
            data=json.dumps(payload).encode("utf-8"),
            headers={"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_create) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            print(f"Successfully created '{name}' (ID: {res.get('id')})")
            return res

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    wfs = [
        os.path.join(current_dir, "oog_survey_ingestion_sensor.json"),
        os.path.join(current_dir, "oog_permit_notification_executor.json")
    ]
    for wf in wfs:
        if os.path.exists(wf):
            try:
                deploy_workflow(wf)
            except Exception as e:
                print(f"Failed to deploy {wf}: {e}")
