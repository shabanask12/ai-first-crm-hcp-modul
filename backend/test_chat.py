import os
from fastapi.testclient import TestClient
from main import app
from dotenv import load_dotenv

load_dotenv()

client = TestClient(app)

payload = {
    "messages": [
        {"sender": "user", "text": "Search for cardiology doctors"}
    ],
    "form_draft": {
        "hcp_id": None,
        "hcp_name": "",
        "type": "Meeting",
        "date": "2026-07-10",
        "time": "14:00",
        "attendees": "",
        "topics": "",
        "sentiment": "Neutral",
        "outcomes": "",
        "follow_ups": "",
        "material_ids": []
    },
    "current_hcp_id": None,
    "current_interaction_id": None
}

try:
    print("Sending request to /api/chat...")
    response = client.post("/api/chat", json=payload)
    print("Response Status Code:", response.status_code)
    print("Response JSON:")
    print(response.json())
except Exception as e:
    print("Error:")
    import traceback
    traceback.print_exc()
