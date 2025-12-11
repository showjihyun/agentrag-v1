#!/usr/bin/env python3
"""
Generate comprehensive API documentation from OpenAPI spec.

This script:
1. Extracts OpenAPI spec from FastAPI app
2. Generates Markdown documentation
3. Creates example code snippets
4. Generates Postman collection
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
from backend.main import app


def get_openapi_spec() -> Dict[str, Any]:
    """Get OpenAPI specification from FastAPI app."""
    return app.openapi()


def generate_markdown_docs(spec: Dict[str, Any]) -> str:
    """Generate Markdown documentation from OpenAPI spec."""
    
    md = []
    md.append(f"# {spec['info']['title']}")
    md.append(f"\n**Version**: {spec['info']['version']}")
    md.append(f"\n**Description**: {spec['info']['description']}\n")
    
    # Table of contents
    md.append("## Table of Contents\n")
    for tag in spec.get('tags', []):
        md.append(f"- [{tag['name']}](#{tag['name'].lower().replace(' ', '-')})")
    md.append("")
    
    # Group endpoints by tag
    endpoints_by_tag: Dict[str, List] = {}
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if method in ['get', 'post', 'put', 'delete', 'patch']:
                tag = details.get('tags', ['Other'])[0]
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                endpoints_by_tag[tag].append({
                    'path': path,
                    'method': method.upper(),
                    'details': details
                })
    
    # Generate documentation for each tag
    for tag, endpoints in endpoints_by_tag.items():
        md.append(f"## {tag}\n")
        
        for endpoint in endpoints:
            path = endpoint['path']
            method = endpoint['method']
            details = endpoint['details']
            
            # Endpoint header
            md.append(f"### {method} {path}\n")
            md.append(f"**Summary**: {details.get('summary', 'No summary')}\n")
            
            if 'description' in details:
                md.append(f"{details['description']}\n")
            
            # Parameters
            if 'parameters' in details:
                md.append("**Parameters**:\n")
                for param in details['parameters']:
                    required = " (required)" if param.get('required') else ""
                    md.append(f"- `{param['name']}` ({param['in']}){required}: {param.get('description', '')}")
                md.append("")
            
            # Request body
            if 'requestBody' in details:
                md.append("**Request Body**:\n")
                content = details['requestBody'].get('content', {})
                for content_type, schema_info in content.items():
                    md.append(f"Content-Type: `{content_type}`\n")
                    if 'schema' in schema_info:
                        md.append("```json")
                        md.append(json.dumps(get_example_from_schema(schema_info['schema'], spec), indent=2))
                        md.append("```\n")
            
            # Responses
            if 'responses' in details:
                md.append("**Responses**:\n")
                for status_code, response in details['responses'].items():
                    md.append(f"- `{status_code}`: {response.get('description', '')}")
                md.append("")
            
            # Example
            md.append("**Example**:\n")
            md.append("```bash")
            md.append(generate_curl_example(method, path, details))
            md.append("```\n")
            
            md.append("---\n")
    
    return "\n".join(md)


def get_example_from_schema(schema: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
    """Generate example data from JSON schema."""
    
    # Handle $ref
    if '$ref' in schema:
        ref_path = schema['$ref'].split('/')
        ref_schema = spec
        for part in ref_path[1:]:  # Skip '#'
            ref_schema = ref_schema[part]
        return get_example_from_schema(ref_schema, spec)
    
    # Handle different types
    schema_type = schema.get('type', 'object')
    
    if schema_type == 'object':
        example = {}
        properties = schema.get('properties', {})
        for prop_name, prop_schema in properties.items():
            if 'example' in prop_schema:
                example[prop_name] = prop_schema['example']
            else:
                example[prop_name] = get_example_value(prop_schema)
        return example
    
    elif schema_type == 'array':
        items = schema.get('items', {})
        return [get_example_from_schema(items, spec)]
    
    else:
        return get_example_value(schema)


def get_example_value(schema: Dict[str, Any]) -> Any:
    """Get example value for a schema type."""
    
    if 'example' in schema:
        return schema['example']
    
    schema_type = schema.get('type', 'string')
    
    examples = {
        'string': 'example',
        'integer': 1,
        'number': 1.0,
        'boolean': True,
        'array': [],
        'object': {}
    }
    
    return examples.get(schema_type, 'example')


def generate_curl_example(method: str, path: str, details: Dict[str, Any]) -> str:
    """Generate curl command example."""
    
    curl = f"curl -X {method} 'http://localhost:8000{path}'"
    
    # Add headers
    curl += " \\\n  -H 'Authorization: Bearer YOUR_TOKEN'"
    curl += " \\\n  -H 'Content-Type: application/json'"
    
    # Add request body
    if 'requestBody' in details:
        content = details['requestBody'].get('content', {})
        for content_type, schema_info in content.items():
            if 'schema' in schema_info:
                example = get_example_from_schema(schema_info['schema'], {})
                curl += " \\\n  -d '" + json.dumps(example, indent=2) + "'"
                break
    
    return curl


def generate_postman_collection(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Postman collection from OpenAPI spec."""
    
    collection = {
        "info": {
            "name": spec['info']['title'],
            "description": spec['info']['description'],
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }
    
    # Group by tag
    folders: Dict[str, List] = {}
    
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            if method in ['get', 'post', 'put', 'delete', 'patch']:
                tag = details.get('tags', ['Other'])[0]
                
                if tag not in folders:
                    folders[tag] = []
                
                request = {
                    "name": details.get('summary', f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [
                            {
                                "key": "Authorization",
                                "value": "Bearer {{token}}",
                                "type": "text"
                            },
                            {
                                "key": "Content-Type",
                                "value": "application/json",
                                "type": "text"
                            }
                        ],
                        "url": {
                            "raw": f"{{{{base_url}}}}{path}",
                            "host": ["{{base_url}}"],
                            "path": path.split('/')[1:]
                        }
                    }
                }
                
                # Add request body
                if 'requestBody' in details:
                    content = details['requestBody'].get('content', {})
                    for content_type, schema_info in content.items():
                        if 'schema' in schema_info:
                            example = get_example_from_schema(schema_info['schema'], spec)
                            request['request']['body'] = {
                                "mode": "raw",
                                "raw": json.dumps(example, indent=2)
                            }
                            break
                
                folders[tag].append(request)
    
    # Add folders to collection
    for tag, requests in folders.items():
        collection['item'].append({
            "name": tag,
            "item": requests
        })
    
    return collection


def main():
    """Main function to generate all documentation."""
    
    print("Generating API documentation...")
    
    # Get OpenAPI spec
    spec = get_openapi_spec()
    
    # Create docs directory
    docs_dir = Path("docs/api")
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    # Save OpenAPI spec (JSON)
    with open(docs_dir / "openapi.json", "w") as f:
        json.dump(spec, f, indent=2)
    print(f"✓ Generated: {docs_dir / 'openapi.json'}")
    
    # Save OpenAPI spec (YAML)
    with open(docs_dir / "openapi.yaml", "w") as f:
        yaml.dump(spec, f, default_flow_style=False)
    print(f"✓ Generated: {docs_dir / 'openapi.yaml'}")
    
    # Generate Markdown documentation
    markdown = generate_markdown_docs(spec)
    with open(docs_dir / "API.md", "w") as f:
        f.write(markdown)
    print(f"✓ Generated: {docs_dir / 'API.md'}")
    
    # Generate Postman collection
    postman = generate_postman_collection(spec)
    with open(docs_dir / "postman_collection.json", "w") as f:
        json.dump(postman, f, indent=2)
    print(f"✓ Generated: {docs_dir / 'postman_collection.json'}")
    
    print("\n✅ API documentation generated successfully!")
    print(f"\nDocumentation available at:")
    print(f"  - Markdown: {docs_dir / 'API.md'}")
    print(f"  - OpenAPI JSON: {docs_dir / 'openapi.json'}")
    print(f"  - OpenAPI YAML: {docs_dir / 'openapi.yaml'}")
    print(f"  - Postman Collection: {docs_dir / 'postman_collection.json'}")


if __name__ == "__main__":
    main()
