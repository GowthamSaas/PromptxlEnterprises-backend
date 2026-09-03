from typing import Any
import time
import httpx
from sqlalchemy.orm import Session

from app.ai_agent.crud import get_endpoint
from app.ai_agent.encryption import decrypt_api_token


# ============================================================
# CONFIG
# ============================================================

DEFAULT_TIMEOUT = 120.0  # 2 minutes for external APIs

ALLOWED_METHODS = {
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
}


# ============================================================
# HEADERS
# ============================================================

def _build_headers(
    api_token: str,
    tenant: str,
) -> dict[str, str]:
    """
    Build headers required by the external API.
    """

    if not api_token:
        raise ValueError(
            "API token is required."
        )

    if not tenant:
        raise ValueError(
            "External tenant is required."
        )

    return {
        "x-api-token": api_token,
        "Tenant": tenant,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


# ============================================================
# METHOD VALIDATION
# ============================================================

def _normalize_method(
    method: str | None,
) -> str:
    """
    Normalize and validate HTTP method.
    """

    if not method:
        return "GET"

    method = method.strip().upper()

    if method not in ALLOWED_METHODS:
        raise ValueError(
            f"Unsupported HTTP method: {method}. "
            f"Allowed methods: "
            f"{', '.join(sorted(ALLOWED_METHODS))}"
        )

    return method


# ============================================================
# URL VALIDATION
# ============================================================

def _validate_url(
    endpoint: str,
) -> str:
    """
    Validate external endpoint URL.
    """

    if not endpoint:
        raise ValueError(
            "Endpoint URL is required."
        )

    endpoint = endpoint.strip()

    if not (
        endpoint.startswith("http://")
        or endpoint.startswith("https://")
    ):
        raise ValueError(
            "Endpoint must start with "
            "http:// or https://"
        )

    return endpoint


# ============================================================
# RESPONSE PARSER
# ============================================================

def _parse_response(
    response: httpx.Response,
) -> Any:
    """
    Parse external API response.

    Supports:
        application/json
        JSON without content-type
        plain text
        empty response
    """

    # --------------------------------------------------------
    # Empty response
    # --------------------------------------------------------

    if not response.content:
        return None

    content_type = (
        response.headers
        .get(
            "content-type",
            "",
        )
        .lower()
    )

    # --------------------------------------------------------
    # JSON response
    # --------------------------------------------------------

    if "application/json" in content_type:

        try:
            return response.json()

        except ValueError:
            pass

    # --------------------------------------------------------
    # Try JSON even if content-type is wrong
    # --------------------------------------------------------

    try:
        return response.json()

    except ValueError:
        pass

    # --------------------------------------------------------
    # Plain text
    # --------------------------------------------------------

    return response.text


# ============================================================
# HTTP REQUEST
# ============================================================

# Configure a reasonable timeout for external APIs
# 30 seconds total, 10 seconds for connection
EXTERNAL_API_TIMEOUT = httpx.Timeout(
    connect=10.0,
    read=30.0,
    write=30.0,
    pool=10.0,
)


def _send_request(
    endpoint: str,
    headers: dict[str, str],
    method: str,
    payload: dict | list | None = None,
) -> httpx.Response:

    method = _normalize_method(method)
    endpoint = _validate_url(endpoint)

    start = time.time()

    # Redacted headers for logging (hide x-api-token)
    log_headers = {k: ("[REDACTED]" if k.lower() == "x-api-token" else v) for k, v in headers.items()}

    try:

        with httpx.Client(
            timeout=EXTERNAL_API_TIMEOUT,
            follow_redirects=True,
        ) as client:

            print("\n" + "=" * 50)
            print("HTTP CLIENT DEBUG")
            print("=" * 50)
            print(f"URL: {endpoint}")
            print(f"METHOD: {method}")
            print(f"TIMEOUT: {EXTERNAL_API_TIMEOUT}")
            print(f"HEADERS: {log_headers}")
            print(f"REQUEST BODY: {payload if method != 'GET' else 'none (GET)'}")
            print("=" * 50)

            response = client.request(
                method=method,
                url=endpoint,
                headers=headers,
                json=payload if method != "GET" else None,
            )

            elapsed = time.time() - start

            print("\n" + "=" * 50)
            print("HTTP CLIENT DEBUG - RESPONSE")
            print("=" * 50)
            print(f"STATUS CODE: {response.status_code}")
            print(f"ELAPSED TIME: {elapsed:.2f} seconds")
            print(f"RESPONSE: {response.text[:500] if response.text else 'empty'}")
            print("=" * 50 + "\n")

            return response

    except httpx.TimeoutException as exc:

        elapsed = time.time() - start
        print("\n" + "=" * 50)
        print("HTTP CLIENT DEBUG - TIMEOUT")
        print("=" * 50)
        print(f"URL: {endpoint}")
        print(f"ELAPSED TIME: {elapsed:.2f} seconds")
        print(f"TIMEOUT CONFIG: {EXTERNAL_API_TIMEOUT}")
        print("=" * 50 + "\n")

        raise ValueError(
            "The external API is taking too long to respond. "
            "This could mean the API is slow or unavailable right now. "
            "Please try again in a few moments."
        ) from exc

    except httpx.ConnectError as exc:

        elapsed = time.time() - start
        print("\n" + "=" * 50)
        print("HTTP CLIENT DEBUG - CONNECT ERROR")
        print("=" * 50)
        print(f"URL: {endpoint}")
        print(f"ELAPSED TIME: {elapsed:.2f} seconds")
        print(f"ERROR: {exc}")
        print("=" * 50 + "\n")

        raise ValueError(
            f"Cannot reach the external API at {endpoint}. "
            "Please check if the API URL is correct and the service is running."
        ) from exc

    except httpx.RequestError as exc:

        elapsed = time.time() - start
        print("\n" + "=" * 50)
        print("HTTP CLIENT DEBUG - REQUEST ERROR")
        print("=" * 50)
        print(f"URL: {endpoint}")
        print(f"ELAPSED TIME: {elapsed:.2f} seconds")
        print(f"ERROR: {exc}")
        print("=" * 50 + "\n")

        raise ValueError(
            f"Unable to connect to external endpoint: {exc}"
        ) from exc

# ============================================================
# RESPONSE VALIDATION
# ============================================================

def _validate_response(
    response: httpx.Response,
) -> Any:
    """
    Parse and validate external API response.
    """

    response_data = _parse_response(
        response
    )

    # --------------------------------------------------------
    # External API error
    # --------------------------------------------------------

    if not response.is_success:

        raise ValueError(
            f"External API returned "
            f"{response.status_code}: "
            f"{response_data}"
        )

    return response_data


# ============================================================
# CONNECTED ENDPOINT
# ============================================================

def call_endpoint(
    db: Session,
    connection,
    endpoint_id: int,
    tenant: str,
    method: str = "GET",
    payload: dict | list | None = None,
) -> dict:
    """
    Call a connected external API endpoint.

    The endpoint is stored in the database.

    API token:
        Decrypted only in memory.

    API token:
        Never returned to frontend.
    """

    # ========================================================
    # VALIDATE TENANT
    # ========================================================

    if not tenant or not tenant.strip():

        raise ValueError(
            "External tenant is required."
        )

    tenant = tenant.strip()

    # ========================================================
    # GET ENDPOINT
    # ========================================================

    endpoint_obj = get_endpoint(
        db=db,
        connection_id=connection.id,
        endpoint_id=endpoint_id,
    )

    if not endpoint_obj:

        raise ValueError(
            "Connected endpoint not found."
        )

    # ========================================================
    # ENDPOINT URL
    # ========================================================

    endpoint = _validate_url(
        endpoint_obj.endpoint
    )

    # ========================================================
    # DECRYPT API TOKEN
    # ========================================================

    api_token = decrypt_api_token(
        connection.encrypted_api_token
    )

    if not api_token:

        raise ValueError(
            "Unable to decrypt API token."
        )

    # ========================================================
    # HEADERS
    # ========================================================

    headers = _build_headers(
        api_token=api_token,
        tenant=tenant,
    )

    # ========================================================
    # METHOD
    # ========================================================

    method = _normalize_method(
        method
    )

    # ========================================================
    # REQUEST
    # ========================================================

    response = _send_request(
        endpoint=endpoint,
        headers=headers,
        method=method,
        payload=payload,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    response_data = _validate_response(
        response
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "success": True,
        "status_code": response.status_code,
        "endpoint": endpoint,
        "method": method,
        "data": response_data,
    }


# ============================================================
# DIRECT ENDPOINT
# ============================================================

def call_direct_endpoint(
    api_token: str,
    endpoint: str,
    tenant: str,
    method: str = "GET",
    payload: dict | list | None = None,
) -> dict:
    """
    Call an external API directly.

    This endpoint does NOT need to be stored
    in ai_agent_endpoints table.

    Example:

        User prompt:

        https://api.example.com/api/lists
        get the lists

    The system can directly call:

        GET https://api.example.com/api/lists
    """

    # ========================================================
    # TOKEN
    # ========================================================

    if not api_token:

        raise ValueError(
            "API token is required."
        )

    # ========================================================
    # TENANT
    # ========================================================

    if not tenant or not tenant.strip():

        raise ValueError(
            "External tenant is required."
        )

    tenant = tenant.strip()

    # ========================================================
    # ENDPOINT
    # ========================================================

    endpoint = _validate_url(
        endpoint
    )

    # ========================================================
    # HEADERS
    # ========================================================

    headers = _build_headers(
        api_token=api_token,
        tenant=tenant,
    )

    # ========================================================
    # METHOD
    # ========================================================

    method = _normalize_method(
        method
    )

    # ========================================================
    # REQUEST
    # ========================================================

    response = _send_request(
        endpoint=endpoint,
        headers=headers,
        method=method,
        payload=payload,
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    response_data = _validate_response(
        response
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {
        "success": True,
        "status_code": response.status_code,
        "endpoint": endpoint,
        "method": method,
        "data": response_data,
    }