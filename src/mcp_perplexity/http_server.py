"""HTTP/Streamable-HTTP server entry point for MCP Perplexity server."""
import os
import sys
import asyncio
import logging
import json
from pathlib import Path

from quart import Quart, jsonify, request as quart_request
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions
import mcp.server.streamable_http

from .server import server

# Configure logging
if os.getenv('DEBUG_LOGS', 'false').lower() == 'true':
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
else:
    logging.getLogger().handlers = []
    logging.getLogger().setLevel(logging.CRITICAL)

# Create Quart app
app = Quart(__name__)

# Initialize MCP transport
transport = mcp.server.streamable_http.StreamableHTTPServerTransport("/mcp")


@app.route('/.well-known/mcp/server-card.json')
async def server_card():
    """Serve the MCP server card for Smithery scanning"""
    try:
        project_root = Path(__file__).parent.parent.parent
        server_card_path = project_root / '.well-known' / 'mcp' / 'server-card.json'

        if server_card_path.exists():
            with open(server_card_path, 'r') as f:
                server_card_data = json.load(f)
            return jsonify(server_card_data)
        else:
            logging.error(f"Server card not found at {server_card_path}")
            return jsonify({'error': 'Server card not found'}), 404
    except Exception as e:
        logging.error(f"Error serving server card: {e}")
        return jsonify({'error': 'Failed to load server card'}), 500


@app.route('/mcp', methods=['GET', 'POST', 'OPTIONS'])
async def mcp_endpoint():
    """MCP protocol endpoint using streamable HTTP transport"""
    try:
        # Handle CORS preflight
        if quart_request.method == 'OPTIONS':
            response = await app.make_default_options_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = '*'
            return response

        # Convert Quart request to ASGI scope/receive/send format
        scope = {
            'type': 'http',
            'method': quart_request.method,
            'path': quart_request.path,
            'query_string': quart_request.query_string,
            'headers': [(k.lower().encode(), v.encode()) for k, v in quart_request.headers.items()],
        }

        body = await quart_request.get_data()

        async def receive():
            return {'type': 'http.request', 'body': body}

        response_started = False
        status_code = 200
        response_headers = []
        response_body = bytearray()

        async def send(message):
            nonlocal response_started, status_code, response_headers, response_body
            if message['type'] == 'http.response.start':
                response_started = True
                status_code = message['status']
                response_headers = message.get('headers', [])
            elif message['type'] == 'http.response.body':
                response_body.extend(message.get('body', b''))

        # Call the transport handler
        await transport(scope, receive, send)

        # Build response
        from quart import Response
        resp = Response(bytes(response_body), status=status_code)
        for header_name, header_value in response_headers:
            resp.headers[header_name.decode()] = header_value.decode()

        # Add CORS headers
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    except Exception as e:
        logging.error(f"Error in MCP endpoint: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


async def run_server():
    """Initialize and run the MCP server with HTTP transport"""
    # Initialize the MCP server with the transport
    init_options = InitializationOptions(
        server_name="mcp-server-perplexity",
        server_version="0.5.9",
        capabilities=server.get_capabilities(
            notification_options=NotificationOptions(tools_changed=True),
            experimental_capabilities={},
        ),
    )

    # Connect the server to the transport
    async with transport.connect_read_stream() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


async def main():
    """Main entry point for HTTP server"""
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')

    logging.info(f"Starting HTTP MCP server on {host}:{port}")

    # Start the MCP server task
    server_task = asyncio.create_task(run_server())

    # Start the HTTP server
    from hypercorn.asyncio import serve
    from hypercorn.config import Config

    config = Config()
    config.bind = [f"{host}:{port}"]

    # Configure logging
    if os.getenv('DEBUG_LOGS', 'false').lower() == 'true':
        config.accesslog = logging.getLogger('hypercorn.access')
        config.errorlog = logging.getLogger('hypercorn.error')
    else:
        config.accesslog = None
        config.errorlog = None

    try:
        await serve(app, config)
    finally:
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
