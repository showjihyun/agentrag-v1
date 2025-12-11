"""Custom assertion functions for testing."""

from typing import Any, Dict, List, Optional
import json


def assert_valid_response(response: Any, status_code: int = 200) -> None:
    """Assert that response has expected status code."""
    assert response.status_code == status_code, (
        f"Expected status {status_code}, got {response.status_code}: "
        f"{response.text}"
    )


def assert_json_response(response: Any) -> Dict[str, Any]:
    """Assert response is valid JSON and return parsed data."""
    assert response.headers.get("content-type", "").startswith("application/json"), (
        f"Expected JSON response, got {response.headers.get('content-type')}"
    )
    return response.json()


def assert_error_response(
    response: Any,
    status_code: int,
    error_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Assert error response format."""
    assert_valid_response(response, status_code)
    data = assert_json_response(response)
    
    assert "detail" in data or "message" in data, (
        f"Error response missing detail/message: {data}"
    )
    
    if error_code:
        assert data.get("error_code") == error_code or data.get("error") == error_code, (
            f"Expected error code {error_code}, got {data}"
        )
    
    return data


def assert_pagination_response(
    response: Any,
    expected_total: Optional[int] = None,
) -> Dict[str, Any]:
    """Assert paginated response format."""
    assert_valid_response(response)
    data = assert_json_response(response)
    
    assert "items" in data or "data" in data, (
        f"Pagination response missing items/data: {data}"
    )
    assert "total" in data, f"Pagination response missing total: {data}"
    
    if expected_total is not None:
        assert data["total"] == expected_total, (
            f"Expected total {expected_total}, got {data['total']}"
        )
    
    return data


def assert_contains_keys(data: Dict[str, Any], keys: List[str]) -> None:
    """Assert dictionary contains all specified keys."""
    missing = [k for k in keys if k not in data]
    assert not missing, f"Missing keys: {missing}. Data: {data}"


def assert_list_length(
    items: List[Any],
    expected: int,
    message: str = "",
) -> None:
    """Assert list has expected length."""
    assert len(items) == expected, (
        f"Expected {expected} items, got {len(items)}. {message}"
    )


def assert_response_time(
    response: Any,
    max_seconds: float,
) -> None:
    """Assert response completed within time limit."""
    elapsed = response.elapsed.total_seconds()
    assert elapsed <= max_seconds, (
        f"Response took {elapsed:.2f}s, expected <= {max_seconds}s"
    )
