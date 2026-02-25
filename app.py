#!/usr/bin/env python3
"""
Railway deployment entry point for Autonomous AI System
"""
import os
from AutonomousAI import AutonomousAI
from AIServer import run_server

if __name__ == "__main__":
    # Get port from environment (Railway sets PORT env var)
    port = int(os.environ.get("PORT", 8000))
    
    # Initialize AI system with ephemeral memory dir for Railway
    # (Railway's /tmp persists during dyno lifetime)
    memory_dir = os.environ.get("AI_MEMORY_DIR", "/tmp/ai_memory")
    
    print(f"[Railway] Starting Autonomous AI on port {port}")
    print(f"[Railway] Memory directory: {memory_dir}")
    
    # Create AI instance
    api_key = os.environ.get("OPENAI_API_KEY")
    ai = AutonomousAI(api_key=api_key, memory_dir=memory_dir)
    
    # Start the FastAPI server
    run_server(ai, port=port)
