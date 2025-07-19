# API Documentation

This directory contains comprehensive documentation for the Unified Knowledge Base System API.

## Documentation Files

- `README.md` - Main API documentation with examples and usage instructions
- `openapi.yaml` - OpenAPI 3.0 specification for the API
- `websocket.md` - WebSocket API documentation
- `interactive.html` - Interactive API documentation and testing tool

## Using the Documentation

### OpenAPI Documentation

The OpenAPI specification (`openapi.yaml`) can be used with tools like:

- [Swagger UI](https://swagger.io/tools/swagger-ui/) - For interactive API documentation
- [Redoc](https://redocly.github.io/redoc/) - For beautiful API documentation
- [OpenAPI Generator](https://openapi-generator.tech/) - To generate client libraries

### Interactive Documentation

To use the interactive documentation:

1. Start the API server
2. Open `interactive.html` in a web browser
3. Enter your API key or bearer token if required
4. Test API endpoints directly from the browser

### WebSocket Documentation

The WebSocket documentation (`websocket.md`) provides:

- Connection instructions
- Message formats
- Available operations
- Response types
- Example code in JavaScript and Python

## API Overview

The API is organized into the following sections:

1. **Knowledge Management** - Add, update, retrieve, and delete documents
2. **Query API** - Search and retrieve information from the knowledge base
3. **Administration** - System management and monitoring
4. **User Management** - Manage users and API keys
5. **WebSocket API** - Real-time communication

## Authentication

The API supports two authentication methods:

- API Key Authentication - Via the `X-API-Key` header
- Bearer Token Authentication - Via the `Authorization` header

## Rate Limiting

API requests are subject to rate limiting based on your account tier. Rate limit headers are included in all responses.

## Error Handling

The API uses standard HTTP status codes and provides detailed error information in the response body.

## Examples

See the main documentation file (`README.md`) for comprehensive examples of using the API.

## Generating Client Libraries

You can generate client libraries for various programming languages using the OpenAPI specification:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate a Python client
openapi-generator-cli generate -i openapi.yaml -g python -o ./clients/python

# Generate a JavaScript client
openapi-generator-cli generate -i openapi.yaml -g javascript -o ./clients/javascript
```

## Contributing to the Documentation

When updating the API, please ensure that you also update the documentation:

1. Update the OpenAPI specification (`openapi.yaml`)
2. Update the main documentation (`README.md`)
3. Update the WebSocket documentation (`websocket.md`) if applicable
4. Update the interactive documentation (`interactive.html`) if needed