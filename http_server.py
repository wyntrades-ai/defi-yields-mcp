#!/usr/bin/env python3
"""
HTTP Server Wrapper for DeFi Yields MCP Server

This module provides a FastAPI-based HTTP interface for the DeFi Yields MCP server,
allowing it to run as a streamable HTTP service that can be Dockerized.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import the MCP server functions
from src.defi_yields_mcp import get_yield_pools, analyze_yields

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Request/Response Models
class YieldPoolRequest(BaseModel):
    chain: Optional[str] = Field(None, description="Filter by blockchain (e.g., 'Ethereum', 'Solana')")
    project: Optional[str] = Field(None, description="Filter by project name (e.g., 'lido', 'aave-v3')")

class YieldPool(BaseModel):
    chain: str = Field(..., description="Blockchain name")
    pool: str = Field(..., description="Pool symbol")
    project: str = Field(..., description="Project name")
    tvlUsd: float = Field(..., description="Total Value Locked in USD")
    apy: float = Field(..., description="Annual Percentage Yield")
    apyMean30d: float = Field(..., description="30-day mean APY")
    predictions: Dict[str, Any] = Field(..., description="APY predictions")

class AnalysisRequest(BaseModel):
    chain: Optional[str] = Field(None, description="Filter by blockchain")
    project: Optional[str] = Field(None, description="Filter by project name")

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.1.0"
    uptime: float

# Global variables
startup_time = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global startup_time
    import time
    startup_time = time.time()
    logger.info("DeFi Yields HTTP Server starting up...")

    # Test external API connectivity
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("https://yields.llama.fi/pools")
            response.raise_for_status()
        logger.info("Successfully connected to DefiLlama API")
    except Exception as e:
        logger.error(f"Failed to connect to DefiLlama API: {e}")
        # Continue startup but log the issue

    yield

    logger.info("DeFi Yields HTTP Server shutting down...")

# Create FastAPI app
app = FastAPI(
    title="DeFi Yields MCP HTTP Server",
    description="HTTP API wrapper for DeFi Yields MCP server providing yield pool data from DefiLlama",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import time
    uptime = time.time() - startup_time
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        uptime=uptime
    )

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "name": "DeFi Yields MCP HTTP Server",
        "version": "0.1.0",
        "description": "HTTP API wrapper for DeFi Yields MCP server",
        "endpoints": {
            "health": "/health",
            "pools": "/pools",
            "pools_stream": "/pools/stream",
            "analyze": "/analyze",
            "docs": "/docs"
        }
    }

@app.post("/")
async def mcp_endpoint(request: Dict[str, Any]):
    """
    MCP JSON-RPC endpoint for n8n integration
    Handles MCP protocol requests for tools and prompts
    """
    try:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            # MCP protocol initialization handshake
            client_info = params.get("clientInfo", {})
            logger.info(f"MCP initialization from {client_info.get('name', 'unknown')} v{client_info.get('version', 'unknown')}")

            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {
                    "tools": {},
                    "prompts": {}
                },
                "serverInfo": {
                    "name": "DeFi Yields MCP Server",
                    "version": "0.1.0"
                }
            }

        elif method == "tools/list":
            # List available tools
            result = {
                "tools": [
                    {
                        "name": "get_yield_pools",
                        "description": "Fetch DeFi yield pools from the yields.llama.fi API, optionally filtering by chain or project",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "chain": {
                                    "type": "string",
                                    "description": "Filter for blockchain (e.g., 'Ethereum', 'Solana')"
                                },
                                "project": {
                                    "type": "string",
                                    "description": "Filter for project name (e.g., 'lido', 'aave-v3')"
                                }
                            }
                        }
                    }
                ]
            }

        elif method == "tools/call":
            # Call a tool
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "get_yield_pools":
                # Create a mock context for the MCP function
                class MockContext:
                    def info(self, message: str):
                        logger.info(f"MCP Context: {message}")
                    def error(self, message: str):
                        logger.error(f"MCP Context: {message}")

                pools = await get_yield_pools(
                    chain=arguments.get("chain"),
                    project=arguments.get("project"),
                    ctx=MockContext()
                )

                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(pools, indent=2)
                        }
                    ]
                }
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        elif method == "prompts/list":
            # List available prompts
            result = {
                "prompts": [
                    {
                        "name": "analyze_yields",
                        "description": "Generate a prompt to analyze DeFi yield pools, optionally filtered by chain or project",
                        "arguments": [
                            {
                                "name": "chain",
                                "description": "Optional blockchain filter",
                                "required": False
                            },
                            {
                                "name": "project",
                                "description": "Optional project filter",
                                "required": False
                            }
                        ]
                    }
                ]
            }

        elif method == "prompts/get":
            # Get a specific prompt
            prompt_name = params.get("name")
            arguments = params.get("arguments", {})

            if prompt_name == "analyze_yields":
                chain = arguments.get("chain")
                project = arguments.get("project")

                prompt_text = analyze_yields(chain=chain, project=project)

                result = {
                    "description": prompt_text,
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": prompt_text
                            }
                        }
                    ]
                }
            else:
                raise ValueError(f"Unknown prompt: {prompt_name}")
        else:
            raise ValueError(f"Unknown method: {method}")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    except Exception as e:
        logger.error(f"MCP Error ({method}): {str(e)}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -1,
                "message": str(e)
            }
        }

# Yield pools endpoint
@app.post("/pools", response_model=List[YieldPool])
async def get_pools(request: YieldPoolRequest):
    """
    Get DeFi yield pools with optional filtering

    Args:
        request: YieldPoolRequest with optional chain and project filters
    """
    try:
        # Mock Context for MCP server
        class MockContext:
            def info(self, message: str):
                logger.info(f"MCP Context: {message}")

            def error(self, message: str):
                logger.error(f"MCP Context: {message}")

        pools = await get_yield_pools(
            chain=request.chain,
            project=request.project,
            ctx=MockContext()
        )

        return [YieldPool(**pool) for pool in pools]

    except Exception as e:
        logger.error(f"Error fetching yield pools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GET version of pools endpoint for easier browser testing
@app.get("/pools", response_model=List[YieldPool])
async def get_pools_get(
    chain: Optional[str] = Query(None, description="Filter by blockchain"),
    project: Optional[str] = Query(None, description="Filter by project name")
):
    """GET version of pools endpoint for browser testing"""
    request = YieldPoolRequest(chain=chain, project=project)
    return await get_pools(request)

# Streaming endpoint for yield pools
@app.get("/pools/stream")
async def get_pools_stream(
    chain: Optional[str] = Query(None, description="Filter by blockchain"),
    project: Optional[str] = Query(None, description="Filter by project name")
):
    """Streaming endpoint for yield pools"""

    async def generate_stream():
        try:
            class MockContext:
                def info(self, message: str):
                    logger.info(f"MCP Context: {message}")

                def error(self, message: str):
                    logger.error(f"MCP Context: {message}")

            # Send initial chunk
            yield f"data: {json.dumps({'status': 'fetching', 'message': 'Fetching yield pools...'})}\n\n"

            pools = await get_yield_pools(
                chain=chain,
                project=project,
                ctx=MockContext()
            )

            # Send results as stream
            for i, pool in enumerate(pools):
                chunk = {
                    'status': 'data',
                    'index': i,
                    'total': len(pools),
                    'pool': pool
                }
                yield f"data: {json.dumps(chunk)}\n\n"

            # Send completion signal
            yield f"data: {json.dumps({'status': 'completed', 'total': len(pools)})}\n\n"

        except Exception as e:
            error_chunk = {
                'status': 'error',
                'error': str(e)
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

# Analysis endpoint
@app.post("/analyze", response_model=Dict[str, str])
async def get_analysis(request: AnalysisRequest):
    """Get analysis prompt for yield pools"""
    try:
        analysis_prompt = analyze_yields(chain=request.chain, project=request.project)
        return {"prompt": analysis_prompt}
    except Exception as e:
        logger.error(f"Error generating analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GET version of analyze endpoint
@app.get("/analyze", response_model=Dict[str, str])
async def get_analysis_get(
    chain: Optional[str] = Query(None, description="Filter by blockchain"),
    project: Optional[str] = Query(None, description="Filter by project name")
):
    """GET version of analyze endpoint for browser testing"""
    request = AnalysisRequest(chain=chain, project=project)
    return await get_analysis(request)

# Background task for periodic data refresh
@app.post("/refresh")
async def refresh_data(background_tasks: BackgroundTasks):
    """Trigger background data refresh"""
    async def refresh_task():
        try:
            class MockContext:
                def info(self, message: str):
                    logger.info(f"Background refresh: {message}")

            await get_yield_pools(ctx=MockContext())
            logger.info("Background data refresh completed")
        except Exception as e:
            logger.error(f"Background data refresh failed: {e}")

    background_tasks.add_task(refresh_task)
    return {"status": "refresh_started", "message": "Background refresh initiated"}

if __name__ == "__main__":
    import os

    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))

    logger.info(f"Starting DeFi Yields HTTP Server on {host}:{port}")

    # Run the server
    uvicorn.run(
        "http_server:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_level="info"
    )