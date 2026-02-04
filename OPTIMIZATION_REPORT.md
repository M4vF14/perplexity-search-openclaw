# Optimization Report - Perplexity Search OpenClaw

## Changes Applied

### 1. Performance Optimization in `PerplexityClient`
- **Issue:** The original implementation created a new `httpx.AsyncClient` for every request. This caused unnecessary overhead (TCP/SSL handshakes) and prevented connection pooling.
- **Fix:** Refactored `src/mcp_perplexity/perplexity_client.py` to maintain a persistent `httpx.AsyncClient` instance.
- **Benefit:** Significantly reduced latency for subsequent requests and reduced resource usage.
- **Implementation:**
  - Added `get_client()` method to lazily initialize the client.
  - Added `close()` method to properly cleanup resources.
  - Updated `_stream_completion` to use the shared client.

### 2. Resource Management
- **Issue:** The global `perplexity_client` in the server was never explicitly closed.
- **Fix:** Updated `src/mcp_perplexity/server.py` to call `await perplexity_client.close()` in the `finally` block of the `main()` function.
- **Benefit:** Ensures proper cleanup of network resources when the server shuts down.

### 3. Version Consistency
- **Issue:** `pyproject.toml` specified version `0.5.9` but `src/mcp_perplexity/__init__.py` specified `0.5.8`.
- **Fix:** Updated `src/mcp_perplexity/__init__.py` to `0.5.9`.

## Code Review Findings

- **Web UI:** The Web UI is disabled by default (`WEB_UI_ENABLED=false`), which is appropriate for a standard MCP skill deployment. It has its own database handling in `src/mcp_perplexity/web/database_extension.py` which correctly manages SQLAlchemy sessions and pagination.
- **Database:** Uses `SQLAlchemy` with `QueuePool` and a proper `SessionManager` context manager. This is robust.
- **Error Handling:** Tool calls are wrapped in try-except blocks, preventing the server from crashing on API errors.

## Next Steps

The project is now optimized and ready for deployment.
1. Ensure `PERPLEXITY_API_KEY` is set in the environment where this skill will run.
2. Build the package: `python -m build`
3. Upload to ClawHub.
