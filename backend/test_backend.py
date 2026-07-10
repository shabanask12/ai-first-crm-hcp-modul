import os
import unittest
from fastapi.testclient import TestClient
from main import app
from database import SessionLocal
import models

class TestCRMBackend(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_get_hcps(self):
        """Test retrieving HCPs from database via endpoint."""
        response = self.client.get("/api/hcps")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["name"], "Dr. John Smith")

    def test_get_products(self):
        """Test retrieving products/materials from database."""
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["material_type"], "PDF")

    def test_get_interactions(self):
        """Test retrieving logged interactions."""
        response = self.client.get("/api/interactions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data), 0)
        self.assertEqual(data[0]["type"], "Meeting")
        self.assertEqual(data[0]["sentiment"], "Positive")

    def test_create_and_update_interaction(self):
        """Test manual creation and update of an interaction."""
        # Retrieve first HCP
        hcp = self.db.query(models.HCP).first()
        self.assertIsNotNone(hcp)

        # Create
        payload = {
            "hcp_id": hcp.id,
            "date": "2026-07-10",
            "time": "10:00",
            "type": "Call",
            "attendees": "Dr. John Smith, Rep Bob",
            "topics": "Introductory call to present products.",
            "sentiment": "Neutral",
            "outcomes": "Interpreted positively. Requested email followup.",
            "follow_ups": "Send follow-up details.",
            "material_ids": []
        }
        response = self.client.post("/api/interactions", json=payload)
        self.assertEqual(response.status_code, 200)
        interaction_data = response.json()
        self.assertEqual(interaction_data["type"], "Call")
        interaction_id = interaction_data["id"]

        # Update
        payload["topics"] = "Introductory call - updated topics."
        response_update = self.client.put(f"/api/interactions/{interaction_id}", json=payload)
        self.assertEqual(response_update.status_code, 200)
        updated_data = response_update.json()
        self.assertEqual(updated_data["topics"], "Introductory call - updated topics.")

        # Clean up database entry
        db_interaction = self.db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
        if db_interaction:
            self.db.delete(db_interaction)
            self.db.commit()

if __name__ == "__main__":
    unittest.main()
