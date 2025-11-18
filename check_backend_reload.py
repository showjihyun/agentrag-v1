"""Check if backend has reloaded the changes."""
import requests
import time

API_URL = "http://localhost:8000"

print("🔍 Checking if backend is running...")

try:
    response = requests.get(f"{API_URL}/health", timeout=2)
    if response.status_code == 200:
        print("✅ Backend is running")
        print(f"   Response: {response.json()}")
    else:
        print(f"⚠️  Backend returned status {response.status_code}")
except requests.exceptions.ConnectionError:
    print("❌ Backend is not running!")
    print("   Please start the backend:")
    print("   cd backend")
    print("   uvicorn main:app --reload --port 8000")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("백엔드 재시작 방법:")
print("="*60)
print("1. 백엔드 터미널에서 Ctrl+C")
print("2. 다시 실행: uvicorn main:app --reload --port 8000")
print("   또는: python -m uvicorn main:app --reload --port 8000")
print("\n또는 restart-backend.bat 실행")
