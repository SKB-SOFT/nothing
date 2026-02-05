"""
Dashboard API Routes for Multi-AI Orchestrator
Provides real-time system monitoring, agent status, and error tracking
"""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from collections import deque
import json
import time
import psutil
import asyncio
from enum import Enum
from server.services.metrics_db import MetricsDB

# ==================== MODELS ====================

class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentRequest(BaseModel):
    agent_id: str
    agent_name: str
    timestamp: datetime
    response_time_ms: float
    success: bool
    model: str
    tokens_used: Optional[int] = None

class AgentError(BaseModel):
    agent_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    timestamp: datetime

class SystemMetrics(BaseModel):
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    uptime_seconds: float
    active_agents: int
    total_requests: int
    success_rate: float

# ==================== STATE MANAGEMENT ====================

class DashboardState:
    """In-memory dashboard state with time-series data."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.agent_requests: deque = deque(maxlen=max_history)
        self.agent_errors: deque = deque(maxlen=max_history)
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        self.websocket_connections: List[WebSocket] = []
        
    def add_request(self, agent_id: str, agent_name: str, response_time_ms: float, 
                   success: bool, model: str, tokens_used: Optional[int] = None):
        """Log an agent request."""
        request = AgentRequest(
            agent_id=agent_id,
            agent_name=agent_name,
            timestamp=datetime.now(),
            response_time_ms=response_time_ms,
            success=success,
            model=model,
            tokens_used=tokens_used
        )
        self.agent_requests.append(request)
        
        # Update agent stats
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "name": agent_name,
                "model": model,
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0,
                "last_used": datetime.now(),
                "status": "active"
            }
        
        agent = self.agents[agent_id]
        agent["total_requests"] += 1
        if success:
            agent["successful_requests"] += 1
        else:
            agent["failed_requests"] += 1
        agent["last_used"] = datetime.now()
        
        # Update average response time
        if agent["total_requests"] == 1:
            agent["avg_response_time"] = response_time_ms
        else:
            agent["avg_response_time"] = (
                (agent["avg_response_time"] * (agent["total_requests"] - 1) + response_time_ms) 
                / agent["total_requests"]
            )
    
    def add_error(self, agent_id: str, error_type: str, error_message: str, 
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        """Log an agent error."""
        error = AgentError(
            agent_id=agent_id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            timestamp=datetime.now()
        )
        self.agent_errors.append(error)
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        total_requests = len(self.agent_requests)
        successful_requests = sum(1 for r in self.agent_requests if r.success)
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            memory_available_gb=psutil.virtual_memory().available / (1024**3),
            uptime_seconds=time.time() - self.start_time,
            active_agents=len(self.agents),
            total_requests=total_requests,
            success_rate=success_rate
        )
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent activity (requests + errors combined)."""
        activity = []
        
        # Add recent requests
        for req in list(self.agent_requests)[-limit:]:
            activity.append({
                "type": "request",
                "agent_id": req.agent_id,
                "agent_name": req.agent_name,
                "timestamp": req.timestamp.isoformat(),
                "response_time_ms": req.response_time_ms,
                "success": req.success,
                "model": req.model
            })
        
        # Add recent errors
        for err in list(self.agent_errors)[-limit:]:
            activity.append({
                "type": "error",
                "agent_id": err.agent_id,
                "error_type": err.error_type,
                "error_message": err.error_message,
                "severity": err.severity,
                "timestamp": err.timestamp.isoformat()
            })
        
        # Sort by timestamp descending
        activity.sort(key=lambda x: x["timestamp"], reverse=True)
        return activity[:limit]
    
    def get_agent_stats(self) -> List[Dict[str, Any]]:
        """Get stats for all agents."""
        return [
            {
                "agent_id": agent_id,
                "name": agent["name"],
                "model": agent["model"],
                "total_requests": agent["total_requests"],
                "successful_requests": agent["successful_requests"],
                "failed_requests": agent["failed_requests"],
                "success_rate": (agent["successful_requests"] / agent["total_requests"] * 100) 
                                if agent["total_requests"] > 0 else 0,
                "avg_response_time": round(agent["avg_response_time"], 2),
                "last_used": agent["last_used"].isoformat(),
                "status": agent["status"]
            }
            for agent_id, agent in self.agents.items()
        ]
    
    def get_error_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get error log."""
        return [
            {
                "agent_id": err.agent_id,
                "error_type": err.error_type,
                "error_message": err.error_message,
                "severity": err.severity,
                "timestamp": err.timestamp.isoformat()
            }
            for err in list(self.agent_errors)[-limit:]
        ]

# ==================== GLOBAL STATE ====================

dashboard_state = DashboardState()

# ==================== ROUTES ====================

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/metrics")
async def get_metrics():
    """Get current system metrics."""
    metrics = dashboard_state.get_system_metrics()
    return {
        "cpu_percent": metrics.cpu_percent,
        "memory_percent": metrics.memory_percent,
        "memory_available_gb": round(metrics.memory_available_gb, 2),
        "uptime_seconds": int(metrics.uptime_seconds),
        "active_agents": metrics.active_agents,
        "total_requests": metrics.total_requests,
        "success_rate": round(metrics.success_rate, 2)
    }

@router.get("/activity")
async def get_activity(limit: int = 20):
    """Get recent activity."""
    return {"activity": dashboard_state.get_recent_activity(limit)}

@router.get("/agents")
async def get_agents():
    """Get all agent statistics."""
    return {"agents": dashboard_state.get_agent_stats()}

@router.get("/errors")
async def get_errors(limit: int = 50):
    """Get error log."""
    return {"errors": dashboard_state.get_error_log(limit)}

@router.post("/log-request")
async def log_request(request: AgentRequest):
    """Log an agent request."""
    dashboard_state.add_request(
        agent_id=request.agent_id,
        agent_name=request.agent_name,
        response_time_ms=request.response_time_ms,
        success=request.success,
        model=request.model,
        tokens_used=request.tokens_used
    )
    
    # Broadcast to WebSocket connections
    await broadcast_update({
        "type": "request",
        "data": request.dict()
    })
    
    return {"status": "logged"}

@router.post("/log-error")
async def log_error(error: AgentError):
    """Log an agent error."""
    dashboard_state.add_error(
        agent_id=error.agent_id,
        error_type=error.error_type,
        error_message=error.error_message,
        severity=error.severity
    )
    
    # Broadcast to WebSocket connections
    await broadcast_update({
        "type": "error",
        "data": error.dict()
    })
    
    return {"status": "logged"}

# ==================== REAL METRICS ENDPOINTS ====================
# These return actual data from the metrics database

@router.get("/metrics/timeline")
async def get_metrics_timeline(hours: int = Query(24, ge=1, le=168)):
    """Get raw metrics timeline for the last N hours.
    
    Returns data like:
    [
        {"timestamp": "2026-02-05T10:30:45", "agent": "groq", "latency": 245.5, "success": true, "tokens": 150},
        ...
    ]
    """
    MetricsDB.init()
    return {"metrics": MetricsDB.get_metrics_timeline(hours)}

@router.get("/metrics/agents")
async def get_agent_metrics(hours: int = Query(24, ge=1, le=168)):
    """Get aggregated metrics per agent.
    
    Returns performance stats for each AI provider:
    [
        {
            "agent": "groq",
            "total_requests": 145,
            "successful": 142,
            "failed": 3,
            "success_rate": 97.93,
            "avg_latency_ms": 245.32,
            "min_latency_ms": 150,
            "max_latency_ms": 890,
            "total_tokens": 24560
        },
        ...
    ]
    """
    MetricsDB.init()
    return {"agents": MetricsDB.get_agent_stats(hours)}

@router.get("/metrics/success-rate")
async def get_success_rate(hours: int = Query(24, ge=1, le=168)):
    """Get overall success rate percentage."""
    MetricsDB.init()
    rate = MetricsDB.get_success_rate(hours)
    return {"success_rate": round(rate, 2), "hours": hours}

@router.get("/metrics/latency-percentiles")
async def get_latency_percentiles(hours: int = Query(24, ge=1, le=168)):
    """Get latency percentiles (p50, p95, p99).
    
    Helps you understand if most queries are fast (p50) or if there are slow outliers (p99)
    """
    MetricsDB.init()
    percentiles = MetricsDB.get_latency_percentiles(hours)
    return {
        "p50_ms": round(percentiles["p50"], 2),  # 50% of queries faster than this
        "p95_ms": round(percentiles["p95"], 2),  # 95% of queries faster than this
        "p99_ms": round(percentiles["p99"], 2),  # 99% of queries faster than this
        "avg_ms": round(percentiles["avg"], 2)
    }

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await websocket.accept()
    dashboard_state.websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        dashboard_state.websocket_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in dashboard_state.websocket_connections:
            dashboard_state.websocket_connections.remove(websocket)

# ==================== UTILITIES ====================

async def broadcast_update(message: Dict[str, Any]):
    """Broadcast update to all connected WebSocket clients."""
    disconnected = []
    for connection in dashboard_state.websocket_connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.append(connection)
    
    # Clean up disconnected clients
    for connection in disconnected:
        if connection in dashboard_state.websocket_connections:
            dashboard_state.websocket_connections.remove(connection)

def log_agent_request(agent_id: str, agent_name: str, response_time_ms: float, 
                     success: bool, model: str, tokens_used: Optional[int] = None):
    """Helper function to log agent requests from your orchestrator."""
    dashboard_state.add_request(agent_id, agent_name, response_time_ms, success, model, tokens_used)

def log_agent_error(agent_id: str, error_type: str, error_message: str, 
                   severity: str = "medium"):
    """Helper function to log agent errors from your orchestrator."""
    try:
        severity_enum = ErrorSeverity(severity)
    except ValueError:
        severity_enum = ErrorSeverity.MEDIUM
    
    dashboard_state.add_error(agent_id, error_type, error_message, severity_enum)

# ==================== AGENT MONITORING CLASSES ====================

class MonitoredAgent:
    """Base class for agents that automatically log metrics."""
    
    def __init__(self, agent_id: str, agent_name: str, model: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.model = model
    
    def log_request(self, response_time_ms: float, success: bool, tokens_used: Optional[int] = None):
        """Log a request for this agent."""
        log_agent_request(self.agent_id, self.agent_name, response_time_ms, success, self.model, tokens_used)
    
    def log_error(self, error_type: str, error_message: str, severity: str = "medium"):
        """Log an error for this agent."""
        log_agent_error(self.agent_id, error_type, error_message, severity)

def monitor_agent_call(agent_id: str, agent_name: str, model: str = "unknown"):
    """Decorator to monitor agent function calls."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000
                log_agent_request(agent_id, agent_name, response_time_ms, True, model)
                return result
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                log_agent_error(agent_id, type(e).__name__, str(e), "high")
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                response_time_ms = (time.time() - start_time) * 1000
                log_agent_request(agent_id, agent_name, response_time_ms, True, model)
                return result
            except Exception as e:
                response_time_ms = (time.time() - start_time) * 1000
                log_agent_error(agent_id, type(e).__name__, str(e), "high")
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
