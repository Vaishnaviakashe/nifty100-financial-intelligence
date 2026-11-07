import json
import re
from pathlib import Path

from src.api.main import app

DOCS_DIR = Path("docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

# Generate OpenAPI specification
openapi = app.openapi()

with open(DOCS_DIR / "openapi.json", "w", encoding="utf-8") as f:
    json.dump(openapi, f, indent=2)

# Build Postman collection from OpenAPI paths
items = []
valid_methods = {"get", "post", "put", "patch", "delete", "options", "head"}

for path, operations in openapi.get("paths", {}).items():
    for method, operation in operations.items():
        method_lower = method.lower()

        if method_lower not in valid_methods:
            continue

        # Convert FastAPI path parameters to Postman format
        postman_path = re.sub(r"\{([^}]+)\}", r":\1", path)

        raw_url = "{{base_url}}" + postman_path

        query_params = []
        for parameter in operation.get("parameters", []):
            if parameter.get("in") == "query":
                query_params.append(
                    {
                        "key": parameter["name"],
                        "value": "",
                        "description": parameter.get("description", ""),
                        "disabled": False,
                    }
                )

        url = {
            "raw": raw_url,
            "host": ["{{base_url}}"],
            "path": [
                segment for segment in postman_path.strip("/").split("/") if segment
            ],
        }

        if query_params:
            url["query"] = query_params

        summary = operation.get("summary") or operation.get("operationId") or path

        items.append(
            {
                "name": f"{method.upper()} {path}",
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": url,
                    "description": summary,
                },
                "response": [],
            }
        )

collection = {
    "info": {
        "name": "NIFTY 100 Financial Intelligence API",
        "description": "Complete API collection generated from FastAPI OpenAPI specification.",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    },
    "item": items,
    "variable": [
        {"key": "base_url", "value": "http://127.0.0.1:8000", "type": "string"}
    ],
}

with open(DOCS_DIR / "postman_collection.json", "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=2)

print("OpenAPI paths:", len(openapi.get("paths", {})))
print("Postman requests generated:", len(items))
print("Files generated successfully.")
