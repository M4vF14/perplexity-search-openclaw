import logging
import os
import json
from pathlib import Path
from quart import render_template, jsonify, request
from .database_extension import db

# Setup logging
logger = logging.getLogger(__name__)

# Only enable logging if DEBUG_LOGS is set to true
if os.getenv('DEBUG_LOGS', 'false').lower() == 'true':
    logger.setLevel(logging.INFO)
else:
    logger.setLevel(logging.CRITICAL)  # Effectively disable logging


def register_routes(app):
    @app.route('/')
    async def index():
        try:
            page = request.args.get('page', 1, type=int)
            chats = db.get_all_chats(page=page)
            return await render_template('index.html', chats=chats)
        except Exception as e:
            logger.error(f"Error in index route: {e}")
            return await render_template('error.html', error="Failed to load chats"), 500

    @app.route('/chat/<chat_id>')
    async def chat(chat_id):
        try:
            chat = db.get_chat(chat_id)
            if not chat:
                return await render_template('error.html', error="Chat not found"), 404

            messages = db.get_chat_messages(chat_id)
            return await render_template('chat.html', chat=chat, messages=messages)
        except Exception as e:
            logger.error(f"Error in chat route: {e}")
            return await render_template('error.html', error="Failed to load chat"), 500

    @app.route('/api/chats')
    async def api_chats():
        try:
            page = request.args.get('page', 1, type=int)
            chats = db.get_all_chats(page=page)
            # If it's an HTMX request, return the chat list HTML
            if request.headers.get('HX-Request'):
                return await render_template('_chat_list.html', chats=chats)
            # Otherwise return JSON for API consumers
            return jsonify({
                'chats': [{
                    'id': chat['id'],
                    'title': chat['title'],
                    'created_at': chat['created_at'].isoformat()
                } for chat in chats['chats']],
                'pagination': chats['pagination']
            })
        except Exception as e:
            logger.error(f"Error in api_chats route: {e}")
            return jsonify({'error': 'Failed to load chats'}), 500

    @app.route('/api/chat/<chat_id>/messages')
    async def api_chat_messages(chat_id):
        try:
            messages = db.get_chat_messages(chat_id)
            # If it's an HTMX request, return the messages list HTML
            if request.headers.get('HX-Request'):
                return await render_template('_message_list.html', messages=messages)
            # Otherwise return JSON for API consumers
            return jsonify([{
                'id': msg['id'],
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp'].isoformat()
            } for msg in messages])
        except Exception as e:
            logger.error(f"Error in api_chat_messages route: {e}")
            return jsonify({'error': 'Failed to load messages'}), 500

    @app.route('/api/chat/<chat_id>', methods=['DELETE'])
    async def delete_chat(chat_id):
        try:
            db.delete_chat(chat_id)
            return '', 204
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return jsonify({'error': 'Failed to delete chat'}), 500

    @app.route('/.well-known/mcp/server-card.json')
    async def server_card():
        """Serve the MCP server card for Smithery scanning"""
        try:
            # Get the path to the server-card.json file
            project_root = Path(__file__).parent.parent.parent.parent
            server_card_path = project_root / '.well-known' / 'mcp' / 'server-card.json'

            if server_card_path.exists():
                with open(server_card_path, 'r') as f:
                    server_card_data = json.load(f)
                return jsonify(server_card_data)
            else:
                logger.error(f"Server card not found at {server_card_path}")
                return jsonify({'error': 'Server card not found'}), 404
        except Exception as e:
            logger.error(f"Error serving server card: {e}")
            return jsonify({'error': 'Failed to load server card'}), 500
