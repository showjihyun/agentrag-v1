"""API testing utilities."""

from typing import Any, Dict, Optional
from fastapi.testclient import TestClient


class AuthenticatedClient:
    """Test client wrapper with authentication."""
    
    def __init__(self, client: TestClient, token: Optional[str] = None):
        self.client = client
        self.token = token
    
    def _get_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Get headers with authentication."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if extra_headers:
            headers.update(extra_headers)
        return headers
    
    def get(self, url: str, **kwargs) -> Any:
        """Authenticated GET request."""
        headers = self._get_headers(kwargs.pop("headers", None))
        return self.client.get(url, headers=headers, **kwargs)
    
    def post(self, url: str, **kwargs) -> Any:
        """Authenticated POST request."""
        headers = self._get_headers(kwargs.pop("headers", None))
        return self.client.post(url, headers=headers, **kwargs)
    
    def put(self, url: str, **kwargs) -> Any:
        """Authenticated PUT request."""
        headers = self._get_headers(kwargs.pop("headers", None))
        return self.client.put(url, headers=headers, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Any:
        """Authenticated DELETE request."""
        headers = self._get_headers(kwargs.pop("headers", None))
        return self.client.delete(url, headers=headers, **kwargs)
    
    def login(self, email: str, password: str) -> str:
        """Login and store token."""
        response = self.client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            return self.token
        raise ValueError(f"Login failed: {response.text}")


def create_test_user(
    client: TestClient,
    user_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a test user and return response data."""
    response = client.post("/api/auth/register", json=user_data)
    if response.status_code in (200, 201):
        return response.json()
    raise ValueError(f"User creation failed: {response.text}")


def get_auth_token(
    client: TestClient,
    email: str,
    password: str,
) -> str:
    """Get authentication token for user."""
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    raise ValueError(f"Authentication failed: {response.text}")


def upload_test_document(
    client: TestClient,
    token: str,
    file_content: bytes,
    filename: str = "test.pdf",
    content_type: str = "application/pdf",
) -> Dict[str, Any]:
    """Upload a test document."""
    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, file_content, content_type)},
    )
    if response.status_code in (200, 201):
        return response.json()
    raise ValueError(f"Document upload failed: {response.text}")
