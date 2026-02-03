---
name: perplexity-search
description: Tools for searching the web and managing conversations via Perplexity AI. Use for expert programming assistance, research, debugging, and maintaining persistent chat history with Perplexity.
---

# Perplexity Search Skill

This skill allows you to interact with Perplexity AI for web-based research and expert Q&A.

## Tools

### ask_perplexity
Request expert programming assistance or ask a single question.
- **Use case:** One-off questions, coding solutions, error debugging, technical explanations.
- **Note:** Does not maintain chat history.

### chat_perplexity
Maintain an ongoing conversation with Perplexity AI.
- **Use case:** Multi-turn conversations, research requiring context.
- **Behavior:** Creates a new chat or continues an existing one if a `chat_id` is provided. Returns a `chat_id` for future continuation.

### list_chats_perplexity
List available chat conversations.
- **Returns:** Chat IDs, titles, and relative creation dates.
- **Pagination:** Returns 50 chats per page. Use `page` argument to navigate.

### read_chat_perplexity
Retrieve the complete conversation history for a specific chat.
- **Input:** `chat_id`
- **Returns:** Full chat history with messages and timestamps.
- **Note:** Local read only; does not call Perplexity API.

## Configuration

The skill uses the following environment variables:
- `PERPLEXITY_API_KEY`: Required. Your Perplexity API key.
- `PERPLEXITY_MODEL`: Default model (e.g., `sonar-pro`).
- `PERPLEXITY_MODEL_ASK`: Specific model for `ask_perplexity`.
- `PERPLEXITY_MODEL_CHAT`: Specific model for `chat_perplexity`.

## Best Practices & Limitations

### Source Access
This skill provides comprehensive answers with **citations (URLs)**. Perplexity has already read and synthesized these sources.
- **Recommendation:** Rely on the summaries provided by the tool.
- **Warning:** If you attempt to visit the cited URLs using other tools (like `web_fetch`), you may encounter **403/Access Denied** errors on major news or financial sites that block bots. The inability to scrape a citation does not invalidate the answer provided by Perplexity.

### Context Management
- Use `ask_perplexity` for distinct, unrelated queries to save context.
- Use `chat_perplexity` only when the conversation history is relevant to the follow-up question.
