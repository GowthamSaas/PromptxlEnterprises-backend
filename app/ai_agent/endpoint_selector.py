"""
Endpoint Selector Service for AI Agent

Handles endpoint selection, validation, and authorization.
This service ensures that only authorized endpoints are executed
and that the correct endpoint is selected based on user intent.

Architecture:
    Intent → Candidate Endpoints → Scoring & Selection → Validation → Execution
"""

import json
import re
from typing import Any
from urllib.parse import urlparse

from app.ai_agent.intent_service import Intent, normalize_http_method


# ============================================================
# ENDPOINT SELECTOR
# ============================================================


class EndpointSelector:
    """
    Selects and validates endpoints based on intent and authorized endpoints.
    
    This class implements deterministic endpoint selection that:
    1. Accepts pre-fetched endpoints
    2. Scores each endpoint based on intent match
    3. Validates the selected endpoint against authorization
    4. Returns the validated endpoint for execution
    """
    
    def __init__(
        self,
        endpoints: list[dict],
        intent: Intent,
        method: str | None = None,
    ):
        """
        Initialize with endpoints and intent.
        
        Args:
            endpoints: List of endpoint dicts
            intent: The planned intent
            method: Optional HTTP method override
        """
        self.endpoints = endpoints
        self.intent = intent
        # Use normalize_http_method to safely handle None values
        self.method = normalize_http_method(method or intent.method)
    
    def select_endpoint(self) -> dict | None:
        """
        Select the best endpoint based on intent.
        
        Selection Algorithm:
        1. Filter endpoints by method compatibility
        2. Score by resource name match
        3. Score by path match
        4. Score by collection vs item endpoint
        5. Return highest scoring endpoint
        
        Returns:
            Endpoint dict or None if no match
        """
        if not self.endpoints:
            print(f"\n{'='*60}")
            print(f"ENDPOINT SELECTION FAILED: No endpoints provided")
            print(f"{'='*60}\n")
            return None
        
        # Filter by method first
        method_compatible = [
            ep for ep in self.endpoints
            if (ep.get("method") or "GET").upper() == self.method.upper()
        ]
        
        # If no method match, return None (don't guess)
        if not method_compatible:
            print(f"\n{'='*60}")
            print(f"ENDPOINT SELECTION FAILED: No endpoints with method {self.method}")
            print(f"Available methods: {set(ep.get('method') for ep in self.endpoints)}")
            print(f"{'='*60}\n")
            return None
        
        # Score each endpoint
        scored_endpoints = []
        for ep in method_compatible:
            score, reasons = self._score_endpoint(ep)
            scored_endpoints.append((score, ep, reasons))
        
        # Sort by score descending
        scored_endpoints.sort(key=lambda x: x[0], reverse=True)
        
        best_score, best_endpoint, best_reasons = scored_endpoints[0]

        # MINIMUM SCORE THRESHOLD - prevents weak match selection
        # With resource match: ~220+ (confident)
        # Without resource match: ~55 (weak, should not select)
        MIN_SCORE_THRESHOLD = 100  # Minimum score for valid selection

        if best_score < MIN_SCORE_THRESHOLD:
            print(f"\n{'='*60}")
            print(f"ENDPOINT SELECTION FAILED: Score below minimum threshold")
            print(f"Best score: {best_score} (minimum: {MIN_SCORE_THRESHOLD})")
            print(f"This indicates weak resource match or ambiguous intent")
            print(f"Selected endpoint would be: {best_endpoint.get('endpoint')}")
            print(f"Selection reasons: {best_reasons}")
            print(f"{'='*60}\n")
            return None

        if best_score <= 0:
            print(f"\n{'='*60}")
            print(f"ENDPOINT SELECTION FAILED: All scores <= 0")
            print(f"Best score: {best_score}")
            print(f"{'='*60}\n")
            return None
        
        # Log selection
        print(f"\n{'='*60}")
        print(f"ENDPOINT SELECTED:")
        print(f"  ID: {best_endpoint.get('id')}")
        print(f"  URL: {best_endpoint.get('endpoint')}")
        print(f"  Method: {best_endpoint.get('method')}")
        print(f"  Resource: {best_endpoint.get('resource_name')}")
        print(f"  Score: {best_score}")
        print(f"  Reasons: {', '.join(best_reasons)}")
        print(f"{'='*60}\n")
        
        return best_endpoint
    
    def _score_endpoint(
        self,
        endpoint: dict,
    ) -> tuple[int, list[str]]:
        """
        Score an endpoint based on how well it matches the intent.
        
        Uses self.intent (set during __init__) for intent matching.
        
        Args:
            endpoint: Endpoint dict
            
        Returns:
            Tuple of (score, reasons_list)
        """
        score = 0
        reasons = []
        
        ep_url = endpoint.get("endpoint", "")
        ep_method = (endpoint.get("method") or "GET").upper()
        ep_resource = (endpoint.get("resource_name") or "").lower()
        ep_description = (endpoint.get("description") or "").lower()
        
        parsed_url = urlparse(ep_url)
        ep_path = parsed_url.path.rstrip("/") if parsed_url.path else ""
        path_segments = [s for s in ep_path.strip("/").split("/") if s]
        
        # Check if endpoint has path parameters (item endpoint)
        ep_has_path_params = bool(re.search(r'\{[^}]+\}', ep_path))
        
        # Extract base path (without path parameters)
        ep_base = re.sub(r'\{[^}]+\}', '', ep_path).rstrip("/")
        
        # === RESOURCE NAME MATCH (highest priority) ===
        intent_resource = (self.intent.resource or "").lower().strip()
        has_resource_match = False

        if ep_resource and intent_resource:
            if ep_resource == intent_resource:
                score += 100
                reasons.append("exact resource_name match")
                has_resource_match = True
            elif ep_resource in intent_resource or intent_resource in ep_resource:
                score += 50
                reasons.append("partial resource_name match")
                has_resource_match = True

        # === ACTION-BASED COLLECTION VS ITEM LOGIC ===
        # Resource match is REQUIRED for confident selection
        # Without it, we should NOT select endpoints just based on action/method
        intent_action = (self.intent.action or "list").lower()
        intent_has_target = bool(self.intent.target)

        # Only give full collection/item bonus if we also have a resource match
        # This prevents random endpoint selection when LLM failed to extract resource
        action_bonus = 80 if has_resource_match else 15  # Reduced from 80 to 15 without resource match
        action_penalty = -30 if has_resource_match else -5  # Less penalty without resource match

        # GET on collection (list/get all) - prefer endpoints WITHOUT path params
        if intent_action in ("list", "get") and not intent_has_target:
            if ep_method == "GET":
                if not ep_has_path_params:
                    score += action_bonus
                    reasons.append(f"collection endpoint for list operation (resource_match={has_resource_match})")
                else:
                    score += action_penalty
                    reasons.append("item endpoint rejected for collection operation")

        # GET on specific item (get one) - prefer endpoints WITH path params
        elif intent_action == "get" and intent_has_target:
            if ep_method == "GET":
                if ep_has_path_params:
                    score += action_bonus
                    reasons.append(f"item endpoint for get-one operation (resource_match={has_resource_match})")
                else:
                    score += action_penalty
                    reasons.append("collection endpoint less preferred for item operation")

        # CREATE - only collection endpoints (POST without path params)
        elif intent_action == "create":
            if ep_method == "POST":
                if not ep_has_path_params:
                    score += action_bonus
                    reasons.append(f"collection endpoint for create operation (resource_match={has_resource_match})")
                else:
                    score -= 100
                    reasons.append("item endpoint rejected for create operation")

        # UPDATE - only item endpoints (PATCH/PUT with path params)
        elif intent_action == "update":
            if ep_method in ("PATCH", "PUT"):
                if ep_has_path_params:
                    score += action_bonus
                    reasons.append(f"item endpoint for update operation (resource_match={has_resource_match})")
                else:
                    score -= 100
                    reasons.append("collection endpoint rejected for update operation")

        # DELETE - only item endpoints (DELETE with path params)
        elif intent_action == "delete":
            if ep_method == "DELETE":
                if ep_has_path_params:
                    score += action_bonus
                    reasons.append(f"item endpoint for delete operation (resource_match={has_resource_match})")
                else:
                    score -= 100
                    reasons.append("collection endpoint rejected for delete operation")
        
        # === METHOD EXACT MATCH ===
        if ep_method == self.method.upper():
            score += 40
            reasons.append("method exact match")
        
        # === PATH-BASED MATCHING ===
        intent_target = (self.intent.target or "").lower()
        
        # Check if target matches a path segment
        if intent_target and ep_has_path_params:
            # Check if the target could be a path parameter value
            if intent_target in ep_path.lower():
                score += 30
                reasons.append("target found in endpoint path")
        
        # === DESCRIPTION SEMANTIC MATCH ===
        if intent_resource and intent_resource in ep_description:
            score += 20
            reasons.append("resource in description")
        
        return score, reasons
    
    def validate_endpoint(
        self,
        endpoint_id: int,
        intent: Intent,
        authorized_endpoints: list[dict] | None = None,
    ) -> tuple[bool, dict | None, str | None]:
        """
        Validate that an endpoint is authorized and compatible with intent.
        
        Args:
            endpoint_id: The endpoint ID to validate
            intent: The planned intent
            authorized_endpoints: Pre-fetched endpoints (optional)
            
        Returns:
            Tuple of (is_valid, endpoint_dict, error_message)
        """
        if authorized_endpoints is None:
            authorized_endpoints = self.get_authorized_endpoints()
        
        # Find endpoint by ID
        selected_endpoint = None
        for ep in authorized_endpoints:
            if ep.get("id") == endpoint_id:
                selected_endpoint = ep
                break
        
        if not selected_endpoint:
            return False, None, f"Endpoint ID {endpoint_id} not found or not authorized."
        
        # Validate method
        ep_method = (selected_endpoint.get("method") or "GET").upper()
        if ep_method != intent.method.upper():
            return False, None, (
                f"Method mismatch. Intent requests {intent.method} but "
                f"endpoint supports {ep_method}."
            )
        
        # Validate resource match (optional but recommended)
        ep_resource = (selected_endpoint.get("resource_name") or "").lower()
        intent_resource = (intent.resource or "").lower()
        
        if intent_resource and ep_resource:
            # Allow partial matches but log warning for very different resources
            if ep_resource != intent_resource:
                # Check if they're at least related
                shared_words = set(ep_resource.split()) & set(intent_resource.split())
                if not shared_words:
                    return False, None, (
                        f"Resource mismatch. Intent requests '{intent_resource}' but "
                        f"endpoint is for '{ep_resource}'."
                    )
        
        return True, selected_endpoint, None
    
    def get_endpoint_by_id(
        self,
        endpoint_id: int,
        authorized_endpoints: list[dict] | None = None,
    ) -> dict | None:
        """
        Get endpoint by ID from authorized endpoints.
        
        Args:
            endpoint_id: The endpoint ID
            authorized_endpoints: Pre-fetched endpoints (optional)
            
        Returns:
            Endpoint dict or None
        """
        if authorized_endpoints is None:
            authorized_endpoints = self.get_authorized_endpoints()
        
        for ep in authorized_endpoints:
            if ep.get("id") == endpoint_id:
                return ep
        
        return None


# ============================================================
# SCHEMA LOOKUP
# ============================================================


def get_endpoint_request_schema(
    endpoint: dict | None,
) -> dict | None:
    """
    Get the request schema from an endpoint definition.
    
    This replaces the hardcoded KNOWN_API_SCHEMAS lookup.
    
    Args:
        endpoint: Endpoint dict with request_schema
        
    Returns:
        Request schema dict or None
    """
    if not endpoint:
        return None
    
    schema = endpoint.get("request_schema")
    
    if isinstance(schema, str):
        try:
            return json.loads(schema)
        except json.JSONDecodeError:
            return None
    
    return schema


def get_required_fields(schema: dict | None) -> list[str]:
    """
    Get required fields from a schema.
    
    Args:
        schema: JSON schema dict
        
    Returns:
        List of required field names
    """
    if not schema:
        return []
    
    if isinstance(schema, str):
        try:
            schema = json.loads(schema)
        except json.JSONDecodeError:
            return []
    
    return schema.get("required", [])


def validate_request_body_against_schema(
    request_body: dict | None,
    schema: dict | None,
) -> tuple[bool, list[str]]:
    """
    Validate a request body against an endpoint's schema.
    
    Args:
        request_body: The request body to validate
        schema: The JSON schema to validate against
        
    Returns:
        Tuple of (is_valid, missing_fields)
    """
    if not schema:
        return True, []
    
    request_body = request_body or {}
    required_fields = get_required_fields(schema)
    
    missing = []
    for field in required_fields:
        value = request_body.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    
    return len(missing) == 0, missing


# ============================================================
# TRANSFORMATION
# ============================================================


def transform_request_body_for_endpoint(
    request_body: dict | None,
    endpoint: dict | None,
    method: str,
) -> dict:
    """
    Transform request body for the target endpoint.
    
    This handles field name mapping based on the endpoint's schema.
    Unlike the old hardcoded transform, this derives field names
    from the actual endpoint schema.
    
    Args:
        request_body: Internal request body (snake_case keys)
        endpoint: Target endpoint definition
        method: HTTP method
        
    Returns:
        Transformed request body ready for the external API
    """
    if not request_body:
        return {}
    
    # Safely normalize method before using
    safe_method = normalize_http_method(method)
    
    # For GET/DELETE, no body transformation needed
    if safe_method in ("GET", "DELETE"):
        return {}
    
    if not endpoint:
        # No endpoint info, return as-is
        return request_body
    
    schema = get_endpoint_request_schema(endpoint)
    if not schema:
        # No schema, return as-is
        return request_body
    
    # Get the properties from schema
    properties = schema.get("properties", {})
    
    # Build transformation map based on schema property names
    # The key insight: use the schema's property names as-is
    transformed = {}
    
    for key, value in request_body.items():
        # Check if schema has this exact key
        if key in properties:
            transformed[key] = value
        else:
            # Try to find a matching property (case-insensitive)
            key_lower = key.lower()
            matched = False
            for prop_name in properties:
                if prop_name.lower() == key_lower:
                    transformed[prop_name] = value
                    matched = True
                    break
            if not matched:
                # Keep original key if no match
                transformed[key] = value
    
    return transformed


# ============================================================
# LOGGING
# ============================================================


def log_endpoint_selection(
    intent: Intent,
    authorized_endpoints: list[dict],
    selected_endpoint: dict | None,
    score: int | None,
    reasons: list[str] | None,
):
    """Log endpoint selection for debugging"""
    print(f"\n{'='*60}")
    print(f"ENDPOINT SELECTION DEBUG")
    print(f"{'='*60}")
    print(f"INTENT:")
    print(f"  Action: {intent.action}")
    print(f"  Resource: {intent.resource}")
    print(f"  Method: {intent.method}")
    print(f"  Target: {intent.target}")
    print(f"  Request Body: {intent.request_body}")
    print(f"  Missing Fields: {intent.missing_fields}")
    print(f"")
    print(f"AUTHORIZED ENDPOINTS:")
    for ep in authorized_endpoints:
        print(f"  ID: {ep.get('id')} | {ep.get('method')} | {ep.get('endpoint')} | resource: {ep.get('resource_name')}")
    print(f"")
    if selected_endpoint:
        print(f"SELECTED:")
        print(f"  ID: {selected_endpoint.get('id')}")
        print(f"  URL: {selected_endpoint.get('endpoint')}")
        print(f"  Method: {selected_endpoint.get('method')}")
        print(f"  Score: {score}")
        print(f"  Reasons: {', '.join(reasons or [])}")
    else:
        print(f"NO MATCHING ENDPOINT FOUND")
    print(f"{'='*60}\n")


# Backwards compatibility alias
endpoint_selector = EndpointSelector