"""
Metrics Collection & Storage Service
Captures real performance data from orchestrator calls
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import json

DB_PATH = Path(__file__).parent.parent / "brain.db"

class MetricsDB:
    """SQLite metrics database for persistent storage"""
    
    @staticmethod
    def init():
        """Create metrics tables if they don't exist"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Main metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                tokens_used INTEGER,
                success BOOLEAN NOT NULL,
                model TEXT,
                error_message TEXT
            )
        """)
        
        # Aggregated stats (hourly summaries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics_hourly (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour_start TEXT NOT NULL UNIQUE,
                agent_name TEXT NOT NULL,
                avg_latency_ms REAL,
                max_latency_ms REAL,
                min_latency_ms REAL,
                total_requests INTEGER,
                successful_requests INTEGER,
                failed_requests INTEGER,
                total_tokens INTEGER
            )
        """)
        
        # Create indexes for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
            ON metrics(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_agent 
            ON metrics(agent_name)
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def log_metric(agent_name: str, agent_id: str, latency_ms: float, 
                   success: bool, model: str, tokens_used: Optional[int] = None,
                   error_message: Optional[str] = None):
        """Log a single metric from an orchestrator call"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO metrics 
               (timestamp, agent_name, agent_id, latency_ms, tokens_used, success, model, error_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now().isoformat(), agent_name, agent_id, latency_ms, 
             tokens_used, success, model, error_message)
        )
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_metrics_timeline(hours: int = 24) -> List[Dict[str, Any]]:
        """Get raw metrics for the last N hours"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cursor.execute(
            """SELECT timestamp, agent_name, latency_ms, success, tokens_used, model
               FROM metrics
               WHERE timestamp > ?
               ORDER BY timestamp DESC
               LIMIT 1000""",
            (since,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "timestamp": row[0],
                "agent": row[1],
                "latency": row[2],
                "success": bool(row[3]),
                "tokens": row[4],
                "model": row[5]
            }
            for row in rows
        ]
    
    @staticmethod
    def get_agent_stats(hours: int = 24) -> List[Dict[str, Any]]:
        """Get aggregated stats per agent"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cursor.execute(
            """SELECT agent_name,
                      COUNT(*) as total_requests,
                      SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as successful,
                      SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failed,
                      AVG(latency_ms) as avg_latency,
                      MIN(latency_ms) as min_latency,
                      MAX(latency_ms) as max_latency,
                      SUM(tokens_used) as total_tokens
               FROM metrics
               WHERE timestamp > ?
               GROUP BY agent_name
               ORDER BY total_requests DESC""",
            (since,)
        )
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                "agent": row[0],
                "total_requests": row[1],
                "successful": row[2],
                "failed": row[3],
                "success_rate": (row[2] / row[1] * 100) if row[1] > 0 else 0,
                "avg_latency_ms": round(row[4], 2) if row[4] else 0,
                "min_latency_ms": row[5],
                "max_latency_ms": row[6],
                "total_tokens": row[7] or 0
            }
            for row in rows
        ]
    
    @staticmethod
    def get_success_rate(hours: int = 24) -> float:
        """Get overall success rate"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cursor.execute(
            """SELECT COUNT(*), SUM(CASE WHEN success=1 THEN 1 ELSE 0 END)
               FROM metrics
               WHERE timestamp > ?""",
            (since,)
        )
        
        total, successful = cursor.fetchone()
        conn.close()
        
        return (successful / total * 100) if total > 0 else 0
    
    @staticmethod
    def get_latency_percentiles(hours: int = 24) -> Dict[str, float]:
        """Get latency percentiles (p50, p95, p99)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        cursor.execute(
            """SELECT latency_ms FROM metrics
               WHERE timestamp > ?
               ORDER BY latency_ms ASC""",
            (since,)
        )
        
        latencies = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not latencies:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0}
        
        latencies.sort()
        length = len(latencies)
        
        return {
            "p50": latencies[int(length * 0.5)] if length > 0 else 0,
            "p95": latencies[int(length * 0.95)] if length > 0 else 0,
            "p99": latencies[int(length * 0.99)] if length > 0 else 0,
            "avg": sum(latencies) / length
        }
