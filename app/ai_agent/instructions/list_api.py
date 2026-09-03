"""
List API Instruction File
=========================

This file contains the behavior instructions for the List API endpoint.

The AI Agent uses these instructions when:
1. The user asks to get, show, or fetch lists
2. The user asks to add, create, or insert a list

These instructions are loaded dynamically based on the selected endpoint.

============================================================
ENDPOINT INFO
============================================================

Connected endpoint example:
    GET  /api/lists
    POST /api/lists

============================================================
GET LISTS
============================================================

When the user says:
    "get the lists"
    "show me the lists"
    "list all lists"
    "fetch all lists"
    "show available lists"
    "get all lists"
    "show lists"

The AI must:
    1. Detect this as a GET operation
    2. Use GET method
    3. request_body = null
    4. missing_fields = []
    5. can_execute = true

Output:
{
    "can_execute": true,
    "method": "GET",
    "request_body": null,
    "missing_fields": [],
    "message": ""
}

The AI must NOT:
    - Ask for list_name
    - Ask for standard_list
    - Generate fake list data
    - Pretend to call the API

The backend will call the real API and return actual data.

============================================================
ADD/CREATE LIST (POST)
============================================================

When the user says:
    "add a list"
    "create a list"
    "create new list"
    "add new list"
    "create a new list called X"
    "add X list"
    "create a list named X"

The AI must determine:
    1. Is list_name provided?
    2. Is standard_list provided?

============================================================
REQUEST SCHEMA
============================================================

POST /api/lists

Required fields:
    - list_name (string, required)

Optional fields:
    - standard_list (boolean, default: false)

JSON structure:
{
    "list_name": "string",
    "standard_list": false
}

============================================================
CASE 1: USER PROVIDES EVERYTHING
============================================================

User: "Create a list called Sales and make it standard"

AI extracts:
    list_name = "Sales"
    standard_list = true

Output:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {
        "list_name": "Sales",
        "standard_list": true
    },
    "missing_fields": [],
    "message": ""
}

============================================================
CASE 2: USER PROVIDES ONLY LIST NAME
============================================================

User: "Create a list called Sales"

AI extracts:
    list_name = "Sales"
    standard_list = false (default)

Output:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {
        "list_name": "Sales",
        "standard_list": false
    },
    "missing_fields": [],
    "message": ""
}

NOTE: Do NOT ask "Should it be standard?" when standard_list
has a default value. Just use the default.

============================================================
CASE 3: USER SAYS ONLY "ADD LIST"
============================================================

User: "add a list"

AI detects:
    list_name = MISSING

Output:
{
    "can_execute": false,
    "method": "POST",
    "request_body": null,
    "missing_fields": ["list_name"],
    "message": "What should the list name be?"
}

============================================================
CASE 4: FOLLOW-UP MESSAGE
============================================================

User: "add a list"
AI: "What should the list name be?"
User: "Sales"

AI must:
    1. Recognize "Sales" is answer to the previous question
    2. Preserve the POST operation
    3. Use list_name = "Sales"
    4. standard_list = false (default)

Output:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {
        "list_name": "Sales",
        "standard_list": false
    },
    "missing_fields": [],
    "message": ""
}

============================================================
CASE 5: USER PROVIDES STANDARD = TRUE
============================================================

User: "add a list called Sales, standard true"
User: "add a standard list named Sales"
User: "create Sales and make it standard"

AI extracts:
    list_name = "Sales"
    standard_list = true

Output:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {
        "list_name": "Sales",
        "standard_list": true
    },
    "missing_fields": [],
    "message": ""
}

============================================================
CASE 6: USER PROVIDES STANDARD = FALSE
============================================================

User: "create Sales list, standard false"
User: "create a non-standard list called Sales"

AI extracts:
    list_name = "Sales"
    standard_list = false

Output:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {
        "list_name": "Sales",
        "standard_list": false
    },
    "missing_fields": [],
    "message": ""
}

============================================================
CASE 7: USER PROVIDES ONLY STANDARD
============================================================

User: "add a list and standard true"

AI detects:
    list_name = MISSING
    standard_list = true (provided)

Output:
{
    "can_execute": false,
    "method": "POST",
    "request_body": null,
    "missing_fields": ["list_name"],
    "message": "What should the list name be?"
}

NOTE: Remember standard_list = true for follow-up.

============================================================
CASE 8: USER CHANGES VALUE DURING CONVERSATION
============================================================

User: "add a list"
AI: "What should the list name be?"
User: "Sales"
AI: "Should the list be standard?"
User: "No, make it non-standard"

AI extracts:
    list_name = "Sales"
    standard_list = false (overrides previous)

Output:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {
        "list_name": "Sales",
        "standard_list": false
    },
    "missing_fields": [],
    "message": ""
}

============================================================
DATA EXTRACTION PATTERNS
============================================================

list_name extraction:
    "create X list" → list_name = X
    "add a list named X" → list_name = X
    "create a new list called X" → list_name = X
    "create list X" → list_name = X
    "add X to lists" → list_name = X
    "new list X" → list_name = X

standard_list = true:
    "standard"
    "standard list"
    "make it standard"
    "standard true"
    "yes standard"
    "is standard"

standard_list = false:
    "non-standard"
    "nonstandard"
    "not standard"
    "standard false"
    "no"
    "make it non-standard"

============================================================
BOOLEAN NORMALIZATION
============================================================

Convert to JSON boolean:

true values:
    "true" → true
    "yes" → true
    "standard" → true
    "standard list" → true
    "make it standard" → true

false values:
    "false" → false
    "no" → false
    "non-standard" → false
    "nonstandard" → false
    "not standard" → false
    "make it non-standard" → false

============================================================
IMPORTANT VALIDATION RULES
============================================================

1. list_name is REQUIRED for POST
    If missing → DO NOT execute → Ask user

2. standard_list is OPTIONAL
    Default: false
    If missing → Use false → Do NOT ask

3. NEVER send empty request_body:
    {} → INVALID
    {"list_name": ""} → INVALID

4. NEVER call POST without list_name

5. NEVER pretend API succeeded before it actually did

============================================================
NORMAL CHAT (NO API CALL)
============================================================

If user says:
    "hello"
    "hi"
    "how are you?"
    "what can you do?"

Do NOT call any API.
Respond naturally as chat.

Output:
{
    "can_execute": false,
    "method": null,
    "request_body": null,
    "missing_fields": [],
    "message": "Hello! How can I help you?"
}

============================================================
API RESPONSE HANDLING
============================================================

The backend returns the actual API response.
The AI must ONLY use real API data.

GET success:
    Return actual lists data

POST success:
    "List 'X' was created successfully."

POST error:
    "The list could not be created because: [API error message]"

NEVER fabricate:
    - List IDs
    - Success messages before API response
    - Error messages
    - List names not from API

============================================================
"""

# Full instruction text for the List API
LIST_API_INSTRUCTION_TEXT = """
LIST API BEHAVIOR INSTRUCTIONS
==============================

This instruction applies to: POST /api/lists

SCHEMA:
{
    "list_name": "string (required)",
    "standard_list": "boolean (default: false)"
}

============================================================
GET LISTS (GET /api/lists)
============================================================

When the user says any of:
- "get the lists"
- "show me the lists"
- "list all lists"
- "show lists"
- "get lists"

Action:
- method: GET
- request_body: null
- missing_fields: []
- can_execute: true

============================================================
CREATE LIST (POST /api/lists)
============================================================

STEP 1: Determine list_name
----------------------------
Is list_name provided?

YES - Extract it from the user's message
NO - can_execute = false, ask for list_name

list_name extraction patterns:
- "create a list called X" → X
- "create X list" → X
- "add a list named X" → X
- "create list X" → X
- "add X list" → X

STEP 2: Determine standard_list
--------------------------------
Is standard_list mentioned?

YES - Extract true/false
NO - Use default: false

NOTE: standard_list is OPTIONAL. Do NOT ask for it if not mentioned.
Default is false.

true patterns: "standard", "true", "yes", "make it standard", "is standard"
false patterns: "non-standard", "false", "no", "not standard", "make it non-standard"

============================================================
FOLLOW-UP HANDLING
============================================================

When the user sends a SHORT message (3 words or less) after being asked
for a field value:

1. Check the previous AI output - it contains "missing_fields"
2. The short message IS the answer to that missing field
3. Merge it with any existing request_body

Example:
User: "create a new list"
AI: {"can_execute": false, "missing_fields": ["list_name"], "message": "What should the list name be?"}
User: "Sales"

Action:
- method: POST
- list_name: "Sales" (from the short answer)
- standard_list: false (default)
- request_body: {"list_name": "Sales", "standard_list": false}
- missing_fields: []
- can_execute: true

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON:

For GET or complete POST:
{
    "can_execute": true,
    "method": "POST",
    "request_body": {"list_name": "X", "standard_list": true/false},
    "missing_fields": [],
    "message": ""
}

For incomplete POST (missing list_name):
{
    "can_execute": false,
    "method": "POST",
    "request_body": null,
    "missing_fields": ["list_name"],
    "message": "What should the list name be?"
}

============================================================
IMPORTANT RULES
============================================================

1. list_name is REQUIRED - never execute POST without it
2. standard_list is OPTIONAL - defaults to false
3. NEVER ask for standard_list unless product requires confirmation
4. Short user messages ARE answers to pending questions
5. Preserve POST method from the original conversation
6. Never invent list names or IDs
7. Never pretend API succeeded before it actually did
"""

# Endpoint paths this instruction applies to
LIST_API_PATHS = [
    "/api/lists",
    "/lists",
    "/api/list",
    "/list",
]

# Instruction metadata
INSTRUCTION_NAME = "List API"
INSTRUCTION_VERSION = "1.0.0"

# Schema definition
LIST_API_SCHEMA = {
    "list_name": {
        "type": "string",
        "required": True,
        "description": "Name of the list"
    },
    "standard_list": {
        "type": "boolean",
        "required": False,
        "default": False,
        "description": "Whether the list is standard"
    }
}

# HTTP method detection keywords
GET_KEYWORDS = [
    "get", "show", "list", "fetch", "display", "view", "retrieve"
]

POST_KEYWORDS = [
    "add", "create", "insert", "new"
]

# Natural language patterns for field extraction
LIST_NAME_PATTERNS = [
    # "create X list"
    (r'(?:create|add|make)\s+(?:a\s+)?(?:new\s+)?(?:list\s+)?called?\s+(\w+)', 1),
    # "create list X"
    (r'(?:create|add)\s+(?:a\s+)?(?:new\s+)?list\s+(\w+)', 1),
    # "list named X"
    (r'(?:list|item)\s+(?:named|called)?\s*(\w+)', 1),
    # "X list" (when X is clearly a name, not a keyword)
    (r'^(\w+)\s+list$', 1),
]

# Boolean patterns
STANDARD_TRUE_PATTERNS = [
    r'\b(?:standard|true|yes)\b',
    r'\bmake\s+it\s+standard\b',
    r'\bis\s+standard\b',
]

STANDARD_FALSE_PATTERNS = [
    r'\b(?:non-standard|nonstandard|false|no|not\s+standard)\b',
    r'\bmake\s+it\s+non-standard\b',
    r'\bmake\s+it\s+nonstandard\b',
]


def get_instruction_for_endpoint(endpoint: str) -> dict | None:
    """
    Get the instruction data for a given endpoint path.
    
    Returns instruction dict if endpoint matches List API paths,
    otherwise returns None.
    """
    if not endpoint:
        return None
    
    endpoint_lower = endpoint.lower().strip()
    
    for path in LIST_API_PATHS:
        if path.lower() in endpoint_lower:
            return {
                "name": INSTRUCTION_NAME,
                "version": INSTRUCTION_VERSION,
                "schema": LIST_API_SCHEMA,
                "get_keywords": GET_KEYWORDS,
                "post_keywords": POST_KEYWORDS,
                "list_name_patterns": LIST_NAME_PATTERNS,
                "standard_true_patterns": STANDARD_TRUE_PATTERNS,
                "standard_false_patterns": STANDARD_FALSE_PATTERNS,
                "instruction_text": LIST_API_INSTRUCTION_TEXT,
            }
    
    return None
