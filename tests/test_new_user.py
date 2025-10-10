#!/usr/bin/env python3
"""
Test script to simulate a new user trying to start the bot
"""
import asyncio
import requests
from datetime import datetime

async def test_new_user():
    # Simulate what the bot does when a new user starts
    payload = {
        "id": "999999999",
        "telegramId": "999999999", 
        "username": "testuser123",
        "firstName": "Test",
        "lastName": "User",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": "pending",
    }
    
    backend_url = "http://localhost:5000"
    print(f"Testing: Sending new user to backend: {backend_url}/api/new-users")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(f"{backend_url}/api/new-users", json=payload, timeout=5)
        print(f"Backend response: {response.status_code} - {response.text}")
        
        # Check if it was stored
        get_response = requests.get(f"{backend_url}/api/new-users")
        print(f"Current users: {get_response.json()}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_user())
