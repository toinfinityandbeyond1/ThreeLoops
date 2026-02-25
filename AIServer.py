"""
FastAPI server for Autonomous AI System
Provides REST endpoints and WebSocket streaming for the web UI
"""

import json
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import threading
import time

# Global event loop (will be set during startup)
event_loop = None

# Lifespan context to capture the event loop
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Capture the event loop when the app starts"""
    global event_loop
    event_loop = asyncio.get_event_loop()
    print("[Server] Event loop captured for thread-safe logging")
    
    # Startup logic
    start_log_listener()
    
    yield
    
    # Shutdown logic
    print("[Server] Shutting down")

# Initialize FastAPI app with lifespan
app = FastAPI(title="Autonomous AI Server", version="1.0.0", lifespan=lifespan)

# Enable CORS for localhost frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global AI instance (will be set when server starts)
ai = None

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.lock:
            self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        dead_connections = []
        with self.lock:
            connections_copy = self.active_connections.copy()
        
        for connection in connections_copy:
            try:
                await connection.send_json(message)
            except Exception:
                dead_connections.append(connection)
        
        # Clean up dead connections
        with self.lock:
            for conn in dead_connections:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)

manager = ConnectionManager()

# Start log listener when server starts
def start_log_listener():
    """Add listener to AI's cognitive log for broadcasting to WebSocket clients"""
    if ai and ai.log:
        def broadcast_log(record):
            """Thread-safe broadcast to WebSocket clients"""
            if event_loop and event_loop.is_running():
                # Schedule the coroutine on the main event loop
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": "log", "data": record}),
                    event_loop
                )
        
        ai.log.add_listener(broadcast_log)

# ========================
# REST API ENDPOINTS
# ========================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

@app.get("/status")
async def get_status():
    """Get system status"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        # Get memory counts
        fast_count = ai.fast_memory.collection.count()
        medium_count = ai.medium_memory.collection.count()
        long_term_count = ai.long_term_memory.collection.count()
        
        # Get resource snapshot
        resource_state = ai.resource_monitor.snapshot()
        
        # Get task info
        pending_tasks = len(ai.task_memory.pending) if hasattr(ai, 'task_memory') and ai.task_memory else 0
        
        return {
            "running": ai.running,
            "autonomy_running": ai.autonomy_running,
            "memory": {
                "fast": fast_count,
                "medium": medium_count,
                "long_term": long_term_count
            },
            "resources": {
                "cpu_percent": resource_state.get("cpu_percent", 0),
                "memory_percent": resource_state.get("memory_percent", 0),
                "disk_percent": resource_state.get("disk_percent", 0),
                "network_kbps": resource_state.get("network_kbps", 0),
                "strain": resource_state.get("strain", 0)
            },
            "tasks": {
                "pending": pending_tasks
            },
            "phase": {
                "fast_done": ai.phase_controller.fast_done,
                "medium_done": ai.phase_controller.medium_done,
                "slow_done": ai.phase_controller.slow_done,
                "aligned": ai.phase_controller.check_phase()
            },
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/resources")
async def get_resources():
    """Get current resource snapshot"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        resource_state = ai.resource_monitor.snapshot()
        return {
            "cpu_percent": resource_state.get("cpu_percent", 0),
            "memory_percent": resource_state.get("memory_percent", 0),
            "disk_percent": resource_state.get("disk_percent", 0),
            "network_kbps": resource_state.get("network_kbps", 0),
            "strain": resource_state.get("strain", 0),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/logs")
async def get_logs(limit: int = 50, tier: str = "event"):
    """Get recent logs"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        if tier == "raw":
            logs = ai.log.get_recent_raw(limit)
        elif tier == "event":
            logs = ai.log.get_recent_events(limit)
        else:
            raise ValueError(f"Unknown tier: {tier}")
        
        return {
            "logs": list(logs),
            "count": len(logs),
            "tier": tier,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
async def chat(message: dict):
    """Chat with AI"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        text = message.get("message", "")
        if not text:
            raise ValueError("Message cannot be empty")
        
        ai.mark_user_active()
        response = ai.chat(text)
        
        return {
            "message": text,
            "response": response,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/task")
async def process_task(task: dict):
    """Process a task"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        task_data = task.get("data", [])
        description = task.get("description", "User task")
        
        if not task_data:
            raise ValueError("Task data cannot be empty")
        
        ai.mark_user_active()
        result = ai.process_task(task_data, description)
        
        return {
            "result": result,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/autonomy/start")
async def start_autonomy():
    """Start autonomy loop"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        if not ai.autonomy_running:
            ai.start_autonomy()
        
        return {
            "autonomy_running": ai.autonomy_running,
            "message": "Autonomy loop started",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/autonomy/stop")
async def stop_autonomy():
    """Stop autonomy loop"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        if ai.autonomy_running:
            ai.stop_autonomy()
        
        return {
            "autonomy_running": ai.autonomy_running,
            "message": "Autonomy loop stopped",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/modules")
async def get_modules(limit: int = 10):
    """Get recent modules"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        modules = list(ai.long_term_memory.modules.items())
        modules = modules[-limit:]
        
        result = []
        for module_id, data in modules:
            import numpy as np
            avg_reward = float(np.mean(data["reward_history"])) if data["reward_history"] else 0.0
            result.append({
                "id": module_id,
                "origin": data.get("lesson_origin", "unknown"),
                "versions": len(data.get("versions", [])),
                "avg_reward": avg_reward,
                "usage": len(data.get("reward_history", []))
            })
        
        return {
            "modules": result,
            "count": len(result),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/patterns")
async def get_patterns(limit: int = 10):
    """Get top patterns"""
    if not ai:
        raise HTTPException(status_code=500, detail="AI system not initialized")
    
    try:
        patterns = ai.medium_memory.find_best_patterns(threshold=0.0, limit=limit)
        
        result = []
        for pid, pdata in patterns:
            import numpy as np
            avg_reward = float(np.mean(pdata["reward_history"])) if pdata["reward_history"] else 0.0
            result.append({
                "id": pid,
                "avg_reward": avg_reward,
                "usage": pdata.get("usage_count", 0),
                "code_preview": pdata.get("helper_code", "")[:100]
            })
        
        return {
            "patterns": result,
            "count": len(result),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========================
# WEBSOCKET ENDPOINTS
# ========================

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive, wait for client messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket error: {e}")

@app.websocket("/ws/status")
async def websocket_status(websocket: WebSocket):
    """WebSocket endpoint for real-time status updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Send status every 2 seconds
            if ai:
                resource_state = ai.resource_monitor.snapshot()
                status = {
                    "type": "status",
                    "data": {
                        "cpu_percent": resource_state.get("cpu_percent", 0),
                        "memory_percent": resource_state.get("memory_percent", 0),
                        "disk_percent": resource_state.get("disk_percent", 0),
                        "strain": resource_state.get("strain", 0),
                        "autonomy_running": ai.autonomy_running,
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
                await websocket.send_json(status)
            
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket error: {e}")

# ========================
# SERVER STARTUP
# ========================

def run_server(ai_instance, port=8000):
    """Run the FastAPI server with the given AI instance"""
    global ai
    ai = ai_instance
    
    # Run uvicorn server (lifespan will handle log listener startup)
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    # For testing without AI instance
    print("This module should be imported by AutonomousAI.py")
    print("Run: python AIServer.py with an AI instance as a parameter")
    
    # Example (for development):
    # python -c "from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)"
