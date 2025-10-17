"""Verify that all conversation endpoints require authentication."""

import sys
import requests
from uuid import uuid4

BASE_URL = "http://localhost:8000"


def test_endpoints_require_auth():
    """Test that all conversation endpoints return 401 without authentication."""

    print("Testing conversation endpoints authentication...")
    print("=" * 60)

    # Test data
    session_id = str(uuid4())

    endpoints = [
        ("POST", "/api/conversations/sessions", {"title": "Test"}),
        ("GET", "/api/conversations/sessions", None),
        ("GET", f"/api/conversations/sessions/{session_id}", None),
        ("PUT", f"/api/conversations/sessions/{session_id}", {"title": "Updated"}),
        ("DELETE", f"/api/conversations/sessions/{session_id}", None),
        ("GET", f"/api/conversations/sessions/{session_id}/messages", None),
        ("POST", "/api/conversations/search", {"query": "test"}),
    ]

    all_protected = True

    for method, endpoint, data in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=5)
            elif method == "PUT":
                response = requests.put(f"{BASE_URL}{endpoint}", json=data, timeout=5)
            elif method == "DELETE":
                response = requests.delete(f"{BASE_URL}{endpoint}", timeout=5)

            if response.status_code == 401:
                print(f"✅ {method:6} {endpoint:50} - Protected (401)")
            else:
                print(
                    f"❌ {method:6} {endpoint:50} - NOT Protected ({response.status_code})"
                )
                all_protected = False

        except requests.exceptions.ConnectionError:
            print(f"⚠️  {method:6} {endpoint:50} - Server not running")
            return False
        except Exception as e:
            print(f"❌ {method:6} {endpoint:50} - Error: {e}")
            all_protected = False

    print("=" * 60)

    if all_protected:
        print("✅ All conversation endpoints are properly protected!")
        return True
    else:
        print("❌ Some endpoints are not properly protected!")
        return False


def test_with_valid_token():
    """Test that endpoints work with valid authentication."""

    print("\nTesting with valid authentication...")
    print("=" * 60)

    # First, register a test user
    register_data = {
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "username": f"testuser_{uuid4().hex[:8]}",
        "password": "TestPass123!",
    }

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/register", json=register_data, timeout=5
        )

        if response.status_code != 201:
            print(f"❌ Failed to register test user: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

        token_data = response.json()
        access_token = token_data.get("access_token")

        if not access_token:
            print("❌ No access token in registration response")
            return False

        print(f"✅ Registered test user: {register_data['email']}")

        # Test creating a session with auth
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.post(
            f"{BASE_URL}/api/conversations/sessions",
            json={"title": "Test Session"},
            headers=headers,
            timeout=5,
        )

        if response.status_code == 201:
            session_data = response.json()
            session_id = session_data.get("id")
            print(f"✅ Created session with auth: {session_id}")

            # Test listing sessions
            response = requests.get(
                f"{BASE_URL}/api/conversations/sessions", headers=headers, timeout=5
            )

            if response.status_code == 200:
                sessions = response.json()
                print(f"✅ Listed sessions with auth: {len(sessions)} sessions")
                return True
            else:
                print(f"❌ Failed to list sessions: {response.status_code}")
                return False
        else:
            print(f"❌ Failed to create session with auth: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n🔐 Conversation API Authentication Verification")
    print("=" * 60)

    # Test that endpoints require auth
    protected = test_endpoints_require_auth()

    # Test that endpoints work with valid auth
    works_with_auth = test_with_valid_token()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"All endpoints protected: {'✅ YES' if protected else '❌ NO'}")
    print(f"Works with valid auth:   {'✅ YES' if works_with_auth else '❌ NO'}")
    print("=" * 60)

    if protected and works_with_auth:
        print("\n✅ All conversation endpoints properly require authentication!")
        sys.exit(0)
    else:
        print("\n❌ Authentication verification failed!")
        sys.exit(1)
