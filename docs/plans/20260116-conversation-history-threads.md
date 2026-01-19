# Implementation Plan: Conversation History with Threads

**Created:** 2026-01-16  
**Completed:** 2026-01-19  
**Status:** ✅ Complete

## Problem Statement

Without conversation history, each user question is treated independently with
no context from previous exchanges. Additionally, when multiple users interact
with the bot simultaneously, their messages could mix if using a shared thread.

## Solution Overview

Implement per-session thread isolation using the Azure AI Foundry Agent
Framework's built-in thread support:

1. Frontend generates a unique `session_id` (UUID v4) when user clicks "Start Chat"
2. Backend maintains a `dict[UserSessionId, AgentThread]` mapping
3. Same session ID always gets the same thread (conversation continuity)
4. Different session IDs get separate threads (user isolation)
5. Threads are reset when user clicks "Clear & Restart"

### Goals

- Enable multi-turn conversations with context persistence
- Leverage Agent Framework's native thread support
- Support multiple concurrent conversation sessions
- Isolate conversations between different users/tabs
- Integrate seamlessly with existing QAEngine and API

### Non-Goals

- Local file-based history storage (using server-side threads instead)
- User authentication/authorization (out of scope)
- Conversation analytics or search
- Session expiry/cleanup (future enhancement)

---

## Phase 1: Backend - Session-Based Thread Management ✅

### Task 1.1: Create UserSessionId Type ✅

Create a new type `UserSessionId` based on `str` for type-safe session
identification.

**Files modified:**
- `src/core/qa_engine.py` - Added `UserSessionId = NewType("UserSessionId", str)`

### Task 1.2: Implement Thread Store in QAEngine ✅

Modify `QAEngine` to manage multiple threads using a dictionary keyed by
`UserSessionId`.

**Changes:**
- Added `_threads: dict[UserSessionId, AgentThread]` to store per-session threads
- Added `get_thread(session_id)` method to retrieve or create thread for session
- Updated `invoke()` to accept required `session_id` parameter
- Updated `invoke_streaming()` to accept required `session_id` parameter
- Added `reset_thread(session_id)` method to clear session thread

**Files modified:**
- `src/core/qa_engine.py`

### Task 1.3: Update API Request Models ✅

Update request models to include required `session_id` field.

**Changes:**
- Added `session_id: str` field to `GenerateRequest`
- Created `RestartRequest` model with `session_id: str`

**Files modified:**
- `src/api/generate.py`

### Task 1.4: Update Generate Endpoint ✅

Modify the `/generate` endpoint to pass session ID to QAEngine.

**Files modified:**
- `src/api/generate.py`

### Task 1.5: Update Restart Endpoint ✅

Modify the `/restart` endpoint to accept session ID and reset only that
session's thread.

**Files modified:**
- `src/api/generate.py`

### Task 1.6: Update Backend Tests ✅

Update tests to verify session isolation works correctly.

**New tests added:**
- Test that different session IDs use different threads
- Test that same session ID reuses the same thread
- Test that reset with session ID only affects that session

**Files modified:**
- `tests/core/test_qa_engine.py`
- `tests/api/test_generate.py`
- `tests/api/test_generate_endpoint.py`

---

## Phase 2: Frontend - Session ID Generation and Management ✅

### Task 2.1: Add Session ID Generation Utility ✅

Create a utility function to generate unique session IDs (UUID v4).

**Files created:**
- `src/ui/utils/session.ts` - `generateSessionId()` using `crypto.randomUUID()`

### Task 2.2: Update API Client ✅

Modify `ApiClient` to include session ID in requests.

**Changes:**
- Added `session_id` to `AnswerRequest` interface
- Created `RestartRequest` interface with `session_id`
- Updated `answer()` method to accept `sessionId` parameter
- Updated `restart()` method to accept `sessionId` parameter

**Files modified:**
- `src/ui/utils/api.ts`

### Task 2.3: Update App Component ✅

Integrate session ID management in the main App component.

**Changes:**
- Added `sessionId` state (initially `null`)
- Generate session ID when user clicks "Start Chat"
- Pass session ID to `apiClient.answer()` calls
- Pass session ID to `apiClient.restart()` calls
- Reset session ID to `null` on "Clear & Restart"

**Files modified:**
- `src/ui/App.tsx`

### Task 2.4: Update Frontend Tests ✅

Add tests for session ID handling.

**Files modified:**
- `tests/ui/api.spec.ts` - Updated all tests with session_id, added restart tests
- `tests/ui/session.spec.ts` (new) - Tests for `generateSessionId()` function

---

## Phase 3: Integration Testing ✅

### Task 3.1: Add Integration Test for Session Isolation ✅

Created integration tests that simulate concurrent users with different
session IDs and verify their conversations don't mix.

**Tests added:**
- `test_session_isolation_between_users` - Two users with different sessions
- `test_same_session_maintains_thread` - Same session maintains continuity

**Files modified:**
- `tests/api/test_generate_endpoint.py`

### Task 3.2: Manual Testing

Verify the implementation works:
- [x] Open two browser tabs
- [x] Start chat in both tabs
- [x] Send different questions in each tab
- [x] Verify responses are isolated and don't reference the other tab's questions
- [x] Verify "Clear & Restart" only affects that tab's session

---

## Phase 4: Documentation and Examples

### Task 4.1: Update Sample Scripts

- [ ] Update `samples/basic_qa.py` to demonstrate conversation usage
- [ ] Create `samples/conversation_qa.py` with multi-turn example
- [ ] Show session management patterns

### Task 4.2: Update README

- [ ] Add conversation history section to README.md
- [ ] Document API endpoints for session management
- [ ] Include usage examples

---

## Technical Implementation

### QAEngine Session-Based Thread Management

```python
from typing import NewType
from agent_framework import AgentThread, ChatAgent

UserSessionId = NewType("UserSessionId", str)

class QAEngine:
    def __init__(self, agent: ChatAgent, axiom_store: AxiomStore):
        self.agent = agent
        self.axiom_store = axiom_store
        self._threads: dict[UserSessionId, AgentThread] = {}

    def get_thread(self, session_id: UserSessionId) -> AgentThread:
        if session_id not in self._threads:
            self._threads[session_id] = self.agent.get_new_thread()
        return self._threads[session_id]

    async def invoke_streaming(self, question: str, session_id: UserSessionId, 
                               reality: list[RealityStatement] | None = None):
        thread = self.get_thread(session_id)
        async for chunk in self.agent.run_stream(prompt, thread=thread, store=True):
            yield process_chunk(chunk)

    async def reset_thread(self, session_id: UserSessionId) -> None:
        self._threads[session_id] = self.agent.get_new_thread()
```

### API Request Models

```python
class GenerateRequest(BaseModel):
    question: str = Field(..., min_length=1)
    reality: Reality | None = None
    session_id: str = Field(..., min_length=1)

class RestartRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
```

### Frontend Session Generation

```typescript
// src/ui/utils/session.ts
export function generateSessionId(): string {
  return crypto.randomUUID();
}

// src/ui/App.tsx
const [sessionId, setSessionId] = useState<string | null>(null);

const handleStartChat = () => {
  setSessionId(generateSessionId());
  setIsContextLocked(true);
};

const handleClearAndRestart = async () => {
  if (sessionId) {
    await apiClient.restart(sessionId);
  }
  setSessionId(null);
};
```

---

## Test Results

- **103 Python tests passing** (including session isolation tests)
- **22 frontend tests passing** (including session utility tests)
- TypeScript compiles without errors
- Python linting passes

---

## Success Criteria ✅

- [x] Each browser session gets a unique session ID
- [x] Messages from different sessions are stored in separate threads
- [x] Restarting one session doesn't affect other sessions
- [x] All existing tests pass
- [x] New tests for session isolation pass
- [x] TypeScript compilation succeeds without errors
- [x] Python linting passes

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
| Memory growth from thread dict | Low | Add session cleanup/expiry (future) |
