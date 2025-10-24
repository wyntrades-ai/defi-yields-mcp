# DeFi Yields MCP

An MCP server for AI agents to explore DeFi yield opportunities, powered by DefiLlama.

[![Discord](https://img.shields.io/discord/1353556181251133481?cacheSeconds=3600)](https://discord.gg/aRnuu2eJ)
![GitHub License](https://img.shields.io/github/license/kukapay/defi-yields-mcp)
![Python Version](https://img.shields.io/badge/python-3.10+-blue)
![Docker](https://img.shields.io/badge/docker-ready-blue)
![Status](https://img.shields.io/badge/status-active-brightgreen.svg)

## Features

- **Data Fetching Tool**: The `get_yield_pools` tool retrieves DeFi yield pool data from the DefiLlama, allowing filtering by chain (e.g., Ethereum, Solana) or project (e.g., Lido, Aave).
- **Analysis Prompt**: The `analyze_yields` prompt generates tailored instructions for AI agents to analyze yield pool data, focusing on key metrics like APY, 30-day mean APY, and predictions.
- **HTTP Server Support**: FastAPI-based HTTP server for web integrations and n8n compatibility.
- **Docker Support**: Full Dockerization with multi-stage builds and security best practices.
- **MCP Protocol**: Full Model Context Protocol implementation with JSON-RPC 2.0 support.

## Installation

### MCP Server (Claude Desktop)

To use the server with Claude Desktop, you can either install it automatically or manually configure the Claude Desktop configuration file.

#### Option 1: Automatic Installation
Install the server for Claude Desktop:
```bash
uvx mcp install -m defi_yields_mcp --name "DeFi Yields Server"
```

#### Option 2: Manual Configuration

Locate the configuration file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the server configuration:

```json
{
 "mcpServers": {
   "defi-yields-mcp": {
     "command": "uvx",
     "args": [ "defi-yields-mcp" ]
   }
 }
}
```

Restart Claude Desktop.

### HTTP Server (Web/n8n Integration)

The HTTP server provides a REST API and MCP JSON-RPC endpoint for web integrations, including n8n workflows.

#### Docker Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/kukapay/defi-yields-mcp.git
cd defi-yields-mcp

# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t defi-yields-mcp-http .
docker run -p 8000:8000 defi-yields-mcp-http
```

#### Local Development

```bash
# Install dependencies
pip install -r requirements-http.txt

# Run the HTTP server
python http_server.py
```

The HTTP server will be available at `http://localhost:8000`.

## API Documentation

### REST API Endpoints

- `GET /` - Server information and available endpoints
- `GET /health` - Health check with server status
- `GET /pools` - Get yield pools (supports `chain` and `project` query parameters)
- `POST /pools` - Get yield pools with JSON body
- `GET /pools/stream` - Server-sent events for streaming yield pool data
- `GET /analyze` - Get analysis prompt for yield pools
- `POST /analyze` - Get analysis prompt with JSON body
- `POST /refresh` - Trigger background data refresh
- `POST /` - **MCP JSON-RPC endpoint** for n8n and other MCP clients

### MCP Protocol Support

The HTTP server implements the full MCP JSON-RPC 2.0 protocol:

- `initialize` - Protocol handshake
- `tools/list` - List available tools
- `tools/call` - Execute tools with parameters
- `prompts/list` - List available prompts
- `prompts/get` - Get specific prompts

### Example API Usage

```bash
# Get health status
curl http://localhost:8000/health

# Get Ethereum yield pools
curl "http://localhost:8000/pools?chain=Ethereum"

# MCP tools list
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}'

# MCP tool call
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_yield_pools",
      "arguments": {"chain": "Ethereum"}
    }
  }'
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Server Configuration
PORT=8000
HOST=0.0.0.0
WORKERS=2

# Optional Features
DOMAIN=defi-yields.example.com
NGINX_PORT=80
REDIS_PORT=6379
PROMETHEUS_PORT=9090
API_RATE_LIMIT=100
```

### Docker Compose Services

The `docker-compose.yml` provides several optional services:

- **defi-yields-http** - Main HTTP server (always enabled)
- **nginx** - Reverse proxy for production (enable with `--profile production`)
- **redis** - Caching layer (enable with `--profile cache`)
- **prometheus** - Monitoring (enable with `--profile monitoring`)

```bash
# Enable Redis caching
docker-compose --profile cache up

# Enable production nginx
docker-compose --profile production up

# Enable monitoring
docker-compose --profile monitoring up
```

## Examples

### Claude Desktop (MCP Protocol)

You can use commands like:

- "Fetch yield pools for the Lido project."
- "Analyze yield pools on Ethereum."
- "What are the 30-day mean APYs for Solana pools?"

The `get_yield_pools` tool fetches and filters the data, while the `analyze_yields` prompt guides the LLM to provide a detailed analysis.

### HTTP API / n8n Integration

For web integrations, you can use the REST API or MCP JSON-RPC protocol:

```bash
# REST API call
curl "http://localhost:8000/pools?chain=Ethereum&project=lido"

# MCP JSON-RPC call (for n8n)
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_yield_pools",
      "arguments": {"chain": "Ethereum", "project": "lido"}
    }
  }'
```

### Example Output

Running the `get_yield_pools` tool with a filter for Ethereum:
```json
[
  {
    "chain": "Ethereum",
    "pool": "STETH",
    "project": "lido",
    "tvlUsd": 14804019222,
    "apy": 2.722,
    "apyMean30d": 3.00669,
    "predictions": {
        "predictedClass": "Stable/Up",
        "predictedProbability": 75,
        "binnedConfidence": 3
    }
  },
  ...
]
```

## Security & Production Notes

- **Multi-stage Docker builds** for optimized production images
- **Non-root user** execution in containers
- **Virtual environment** isolation for Python dependencies
- **Health checks** and graceful shutdown handling
- **CORS support** for web integrations
- **Structured logging** for monitoring and debugging

## Development

### Project Structure

```
defi-yields-mcp/
├── src/defi_yields_mcp/
│   ├── __init__.py          # MCP server exports
│   └── cli.py               # FastMCP server implementation
├── http_server.py           # FastAPI HTTP server
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Orchestrated services
├── requirements-http.txt    # HTTP server dependencies
├── requirements.txt         # MCP server dependencies
└── README-HTTP.md           # Detailed HTTP server docs
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
