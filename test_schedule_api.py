from fastapi.testclient import TestClient
from main import app
from datetime import datetime
import json

client = TestClient(app)

def test_get_schedule():
    response = client.get("/api/schedule")
    assert response.status_code == 200
    data = response.json()
    assert "device_id" in data
    assert "slots" in data
    assert "total_cost" in data
    assert "manual_override" in data
    print("Initial Schedule retrieved successfully.")
    print(f"Status: {data['status']}, Total Cost: ${data['total_cost']}")

def test_update_schedule_constraints():
    # Update ready time to 09:00
    new_constraints = {"ready_by_time": "09:00"}
    response = client.post("/api/schedule/update", json={
        "device_id": "EV-001",
        "constraints": new_constraints
    })
    assert response.status_code == 200
    assert response.json()["ready_by"] == "09:00"
    
    # Verify the change is reflected in the schedule
    response = client.get("/api/schedule")
    assert response.json()["ready_by"] == "09:00"
    print("Constraints updated successfully.")

def test_manual_override():
    # Activate override
    response = client.post("/api/schedule/update", json={
        "device_id": "EV-001",
        "manual_override": True
    })
    assert response.status_code == 200
    assert response.json()["manual_override"] == True
    
    # Verify schedule shows override status
    response = client.get("/api/schedule")
    assert response.json()["manual_override"] == True
    assert "Override" in response.json()["status"]
    print("Manual override activated successfully.")

    # Deactivate override
    response = client.post("/api/schedule/update", json={
        "device_id": "EV-001",
        "manual_override": False
    })
    assert response.status_code == 200
    assert response.json()["manual_override"] == False
    print("Manual override deactivated successfully.")

if __name__ == "__main__":
    try:
        test_get_schedule()
        test_update_schedule_constraints()
        test_manual_override()
        print("\nAll integration tests passed!")
    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
