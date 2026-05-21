import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_websocket_text_modality():
    # We use TestClient to connect to the WebSocket endpoint
    with client.websocket_connect("/ws") as websocket:
        # Send a JSON payload with only text modality active
        payload = {
            "active_modalities": ["text"],
            "text": "I am so happy and excited today!"
        }
        websocket.send_text(json.dumps(payload))
        
        # Receive the response
        response = websocket.receive_json()
        
        # Assert the response contains the expected structure
        assert "text_emotions" in response
        assert "fused_emotions" in response
        
        # The fused emotions should have the 7 core emotions
        fused = response["fused_emotions"]
        expected_emotions = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        for emotion in expected_emotions:
            assert emotion in fused

def test_websocket_no_modalities():
    with client.websocket_connect("/ws") as websocket:
        # Send a JSON payload with NO active modalities
        payload = {
            "active_modalities": []
        }
        websocket.send_text(json.dumps(payload))
        
        response = websocket.receive_json()
        
        # Since no modalities are active, fused emotions should all be 0.0
        fused = response["fused_emotions"]
        for emotion, score in fused.items():
            assert score == 0.0
