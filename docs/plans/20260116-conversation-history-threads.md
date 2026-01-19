# Implementation Plan: Conversation History with Threads

**Created:** 2026-01-16  
**Status:** In Progress

## Overview

This plan covers the implementation of conversation history functionality for
the Constitutional QA Agent using the Azure AI Foundry Agent Framework's
built-in thread support. Threads provide server-side conversation management,
eliminating the need for local history storage while enabling multi-turn
conversations.

### Goals

- Enable multi-turn conversations with context persistence
- Leverage Agent Framework's native thread support
- Support multiple concurrent conversation sessions
- Integrate seamlessly with existing QAEngine and API

### Non-Goals

- Local file-based history storage (using server-side threads instead)
- User authentication/authorization (out of scope)
- Conversation analytics or search

---

## Phase 1: QAEngine Thread Support ✅

### - [x] Task 1.1: Add Optional thread_id Parameter to invoke()

- Update `QAEngine.invoke()` method signature to accept optional
  `thread_id: str | None = None` parameter
- When thread_id is provided, pass it to the agent framework to continue
  the conversation
- When thread_id is None, let agent framework create a new thread
- Return tuple of `(response, thread_id)` to allow caller to track the thread

### - [x] Task 1.2: Add Optional thread_id Parameter to invoke_streaming()

- Update `QAEngine.invoke_streaming()` method signature to accept optional
  `thread_id: str | None = None` parameter
- When thread_id is provided, pass it to the agent framework
- When thread_id is None, let agent framework create a new thread
- Update return type to include thread_id alongside streamed content

### - [x] Task 1.3: Update Agent Framework Calls

- Update `agent.run()` and `agent.run_stream()` calls to pass thread_id
- Ensure thread context is properly maintained by the framework
- Handle any thread-related errors gracefully

---

## Phase 2: API Integration

### - [ ] Task 2.1: Update Generate Endpoint for Thread Support

- Update `GenerateRequest` model to include optional `thread_id: str | None`
- Update `generate()` endpoint to:
  - Pass thread_id to QAEngine
  - Include `thread_id` in response for client to use in subsequent requests
- Update response model to include `thread_id` field

---

## Phase 3: Testing

### - [x] Task 3.1: Unit Tests for QAEngine with thread_id

- Update `tests/core/test_qa_engine.py`
- Add tests for:
  - `invoke()` with thread_id parameter
  - `invoke_streaming()` with thread_id parameter
  - Verify thread_id is returned
  - Backward compatibility (None thread_id)

### - [ ] Task 3.2: API Integration Tests

- Update `tests/api/test_generate.py` (or create if needed)
- Test generate endpoint:
  - Generate without thread_id (creates new thread)
  - Generate with thread_id (continues conversation)
  - Response includes thread_id
- Test error handling for invalid thread IDs

### - [ ] Task 3.3: Run All Tests

- Execute full test suite
- Ensure no regressions in existing functionality
- Verify all new tests pass

---

## Phase 4: Documentation and Examples

### - [ ] Task 5.1: Update Sample Scripts

- Update `samples/basic_qa.py` to demonstrate conversation usage
- Create `samples/conversation_qa.py` with multi-turn example
- Show session management patterns

### - [ ] Task 5.2: Update README

- Add conversation history section to README.md
- Document API endpoints for thread management
- Include usage examples

---

### Technical Notes

### Agent Framework Thread API

The Agent Framework handles thread management internally:

```python
# Thread is managed transparently by the agent framework
# Just pass thread_id to run() or run_stream()
async for chunk in agent.run_stream(prompt, thread_id=thread_id):
    ...
```

### Backward Compatibility

All existing functionality remains unchanged. The `thread_id` parameter is
optional - when None, the agent framework creates a new thread automatically.

---

## Dependencies

- No new package dependencies required
- Uses existing `agent-framework` thread capabilities
- Uses existing `pydantic` for models

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Thread API changes in agent-framework | Medium | Pin version, add abstraction layer |
| Thread storage limits | Low | Document limits, add cleanup strategy |
| Performance with long histories | Medium | Limit history window in prompts |
