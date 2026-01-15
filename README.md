# Constitutional Q&A Agent

A Q&A agent for queries, grounded on a constitutional framework. The system
combines three key elements:

- **Constitution**: A static "school of thought" document defining axioms and
  principles that govern the company
- **Reality**: The current state of the world and factual context
- **Question**: User queries that may include hypothetical scenarios,
  potentially overriding aspects of reality or constitution for reasoning
  purposes

The agent leverages Azure OpenAI to provide responses that are consistent with
the constitutional framework while adapting to the given context and
hypothetical scenarios.

## Example Use Case

The agent demonstrates the constitutional framework concept through the banking
domain. In this framework, the "Constitution" is intended to be stable
(unchanging principles), while "Reality" is dynamic (reflecting the current
state of the world):

- **Constitution (stable)**: Company principles that remain constant (e.g., for
  our banking domain:  "Political instability disrupts markets and investor
  confidence")
- **Reality (dynamic)**: Current indicators that change over time (e.g., for
  our banking domain "Current inflation rate in Switzerland is 2.1% as of Q3
  2024")
- **Questions**: Queries from the user, that the Q&A agent should answer
  combining principles with current conditions (e.g., "How might borrowing
  costs be affected for someone seeking a mortgage in Switzerland?")

## Development Environment

This project supports **VS Code Dev Containers** for a consistent development
environment with all dependencies pre-configured.

## Quick Start

**Using Dev Containers (Recommended)**:

1. Open the project in VS Code
1. Reopen in Container when prompted
1. Copy environment template: `cp .env.template .env`
1. Edit `.env` with your Azure OpenAI credentials
1. Run a sample query: `uv run python samples/basic_qa.py`

**Manual Setup**:

1. Copy environment template: `cp .env.template .env`
2. Edit `.env` with your Azure OpenAI credentials
3. Install dependencies: `uv sync`
4. Run a sample query: `uv run python samples/basic_qa.py`

## Project Structure

- `src/core/` - Core QA engine and Azure OpenAI integration
- `src/eval/` - Evaluation experiments and baselines
- `data/` - Constitution and evaluation datasets
- `tests/` - Unit tests

### Port Configuration

The API port is configurable to handle port conflicts and VS Code port forwarding
automatically. The backend writes its actual running port to a configuration file, which the
frontend reads on startup.

1. **Backend startup**: The API reads the `API_PORT` environment variable (defaults to 8080) and
   writes a `.api-config.json` file with the actual port
2. **Frontend startup**: Vite reads `.api-config.json` to determine the correct backend URL
3. **Port forwarding**: Works automatically even when VS Code forwards ports (e.g.,
   8080 → 8081)

#### Configuration

##### Setting a Custom API Port

```bash
# Set port via environment variable
export API_PORT=8081
./bin/serve be
```

Or inline:

```bash
API_PORT=8081 ./bin/serve be
```

##### Using the VS Code Debugger

The VS Code debugger has two configurations for the backend:

1. **Debug Backend API (Port 8080)** - Default port
2. **Debug Backend API (Port 8081)** - Alternative port

Select the appropriate configuration from the debugger dropdown based on which port you want to use.

For full-stack debugging:

- **Debug Full Stack** - Starts backend on port 8080 and frontend on port 8007

Both configurations automatically set the `API_PORT` environment variable and write the
`.api-config.json` file for the frontend.

##### Default Ports

- **Backend API**: 8080 (configurable via `API_PORT`)
- **Frontend Dev Server**: 8007 (configured in
  vite.config.ts)

#### Files

- **`.api-config.json`** (generated): Contains the actual running port
  - Created automatically when the backend starts
  - Ignored by git
  - Read by Vite to configure the frontend

#### Troubleshooting

##### Frontend can't connect to backend

1. **Start backend first**: The frontend needs `.api-config.json` to exist
2. **Check the config file**: Verify `.api-config.json` exists and has the correct port
3. **Restart frontend**: If you change the backend port, restart the frontend dev server

##### Port already in use

```bash
# Use a different port
API_PORT=8081 ./bin/serve be
```

##### VS Code port forwarding issues

The system automatically handles this - just ensure:

1. Backend is running and has written `.api-config.json`
2. Frontend is started after the backend
3. Check VS Code's PORTS tab to see actual forwarded ports
