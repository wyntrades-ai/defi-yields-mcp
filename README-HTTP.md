# DeFi Yields MCP HTTP Server

A FastAPI-based HTTP wrapper for the DeFi Yields MCP server, enabling it to run as a streamable HTTP service that can be Dockerized and deployed in container stacks.

## Features

- **HTTP REST API**: FastAPI-based endpoints for yield pool data
- **MCP Protocol**: Full Model Context Protocol JSON-RPC 2.0 support for n8n integration
- **Streaming Support**: Real-time data streaming with Server-Sent Events
- **Docker Ready**: Multi-stage Dockerfile for production deployment
- **Health Monitoring**: Built-in health checks and monitoring endpoints
- **Scalable**: Support for multiple workers and load balancing
- **CORS Enabled**: Cross-origin resource sharing support
- **Production Ready**: Nginx reverse proxy configuration included

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone and navigate to the project
git clone <repository-url>
cd defi-yields-mcp

# Copy environment configuration
cp .env.example .env

# Start the HTTP server
docker-compose up -d

# Check the service
curl http://localhost:8000/health
```

### Option 2: Direct Docker Build

```bash
# Build the image
docker build -t defi-yields-http .

# Run the container
docker run -d -p 8000:8000 --name defi-yields-http defi-yields-http
```

### Option 3: Local Development

```bash
# Install dependencies
pip install -r requirements-http.txt
pip install -e .

# Run the HTTP server
python http_server.py
```

## API Endpoints

### Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server information and available endpoints |
| GET | `/health` | Health check and server status |
| GET | `/pools` | Get yield pools (GET version) |
| POST | `/pools` | Get yield pools with filters |
| GET | `/pools/stream` | Stream yield pools in real-time |
| GET | `/analyze` | Get analysis prompt (GET version) |
| POST | `/analyze` | Get analysis prompt with filters |
| POST | `/refresh` | Trigger background data refresh |
| POST | `/` | **MCP JSON-RPC endpoint** for n8n and MCP clients |
| GET | `/docs` | Interactive API documentation |

### API Usage Examples

#### Get All Yield Pools
```bash
curl http://localhost:8000/pools
```

#### Filter by Chain
```bash
curl "http://localhost:8000/pools?chain=Ethereum"
```

#### Filter by Project
```bash
curl "http://localhost:8000/pools?project=lido"
```

#### POST Request with Filters
```bash
curl -X POST http://localhost:8000/pools \
  -H "Content-Type: application/json" \
  -d '{"chain": "Ethereum", "project": "lido"}'
```

#### Stream Yield Pools
```bash
curl -N http://localhost:8000/pools/stream?chain=Ethereum
```

#### Get Analysis Prompt
```bash
curl http://localhost:8000/analyze?chain=Solana
```

### MCP Protocol Usage

The HTTP server supports the full MCP JSON-RPC 2.0 protocol for n8n and other MCP clients.

#### MCP Initialize Handshake
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {"tools": {}},
      "clientInfo": {"name": "n8n", "version": "1.0.0"}
    }
  }'
```

#### MCP Tools List
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}'
```

#### MCP Tool Call
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "get_yield_pools",
      "arguments": {"chain": "Ethereum", "project": "lido"}
    }
  }'
```

#### MCP Prompts List
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 4, "method": "prompts/list"}'
```

#### MCP Prompt Get
```bash
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 5,
    "method": "prompts/get",
    "params": {
      "name": "analyze_yields",
      "arguments": {"chain": "Solana"}
    }
  }'
```

## Docker Stack Deployment

### Basic Stack
```bash
docker-compose up -d
```

### Production Stack (with Nginx)
```bash
docker-compose --profile production up -d
```

### Full Stack (with caching and monitoring)
```bash
docker-compose --profile cache --profile monitoring up -d
```

## Configuration

Environment variables can be set in `.env` file or passed directly:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |
| `WORKERS` | `1` | Number of worker processes |
| `DOMAIN` | `localhost` | Domain for Traefik routing |
| `NGINX_PORT` | `80` | Nginx port (production profile) |
| `REDIS_PORT` | `6379` | Redis port (cache profile) |
| `PROMETHEUS_PORT` | `9090` | Prometheus port (monitoring profile) |

## Monitoring and Health

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime": 123.45
}
```

### Prometheus Metrics
When using the monitoring profile, Prometheus metrics are available at:
- Prometheus UI: `http://localhost:9090`
- Health metrics: Scraped from `/health` endpoint

### Docker Health Checks
The container includes built-in health checks that verify:
- HTTP server responsiveness
- External API connectivity
- Service availability

## Production Considerations

### Security
- Configure appropriate CORS origins for production
- Set up proper authentication/authorization
- Use HTTPS in production environments
- Configure rate limiting

### Performance
- Adjust `WORKERS` based on CPU cores
- Enable Redis caching for frequently accessed data
- Use Nginx reverse proxy for load balancing
- Monitor resource usage and scale accordingly

### Reliability
- Set up container restart policies
- Configure health checks with appropriate timeouts
- Use Docker Swarm or Kubernetes for orchestration
- Implement proper logging and monitoring

## Troubleshooting

### Container Issues
```bash
# Check container logs
docker logs defi-yields-http

# Check container status
docker ps

# Execute commands in container
docker exec -it defi-yields-http bash
```

### API Issues
```bash
# Test API connectivity
curl -v http://localhost:8000/health

# Check external API connectivity
curl https://yields.llama.fi/pools
```

### Performance Issues
- Check worker configuration
- Monitor resource usage
- Review external API response times
- Consider enabling caching

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Local Development
```bash
# Install in development mode
pip install -e .

# Run with auto-reload
uvicorn http_server:app --reload --host 0.0.0.0 --port 8000
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.