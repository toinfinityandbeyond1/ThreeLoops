#!/bin/bash
# AUTONOMOUS AI SYSTEM - QUICK START GUIDE

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  AUTONOMOUS AI SYSTEM - QUICK START                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "🔍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "❌ Python not found. Please install Python 3.8+"
        exit 1
    fi
    PYTHON_CMD="python"
else
    PYTHON_CMD="python3"
fi

echo "✓ Python found: $($PYTHON_CMD --version)"
echo ""

# Check/Install dependencies
echo "📦 Installing dependencies..."
$PYTHON_CMD -m pip install -q -r requirements.txt --upgrade
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "⚠️  Warning: Some dependencies may have failed"
fi
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  GETTING STARTED                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "OPTION 1: Run in Interactive CLI Mode (Recommended for first test)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  $PYTHON_CMD AutonomousAI.py"
echo ""
echo "  Then try:"
echo "    AI> help              (show available commands)"
echo "    AI> status            (check system status)"
echo "    AI> chat Hello        (chat with AI)"
echo "    AI> start             (start autonomy loop)"
echo "    AI> stop              (stop autonomy loop)"
echo "    AI> exit              (quit)"
echo ""

echo "OPTION 2: Run with Web Server + React Frontend"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Terminal 1 (API Server):"
echo "  ─────────────────────────"
echo "  $PYTHON_CMD -c \"from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)\""
echo ""
echo "  Terminal 2 (React Frontend):"
echo "  ──────────────────────────────"
echo "  bash create-frontend.sh    # Create React app (one time)"
echo "  cd web-ui"
echo "  npm install               # Install dependencies (first time only)"
echo "  npm start"
echo ""
echo "  Then open: http://localhost:3000"
echo ""

echo "OPTION 3: Test Specific Features"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Test chat functionality:"
echo "  $PYTHON_CMD -c \"from AutonomousAI import AutonomousAI; ai = AutonomousAI(); print(ai.chat('Hello'))\""
echo ""
echo "  Test API endpoints (after starting server):"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/status | $PYTHON_CMD -m json.tool"
echo ""

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  USEFUL LINKS & DOCUMENTATION                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "📚 Documentation Files:"
echo "  • SETUP_AND_USAGE.md      - Complete setup guide"
echo "  • AUTONOMY_REDESIGN.md    - Architecture details"
echo "  • REBUILD_STATUS.md       - Current system status"
echo "  • COMPLETION_REPORT.md    - What was completed today"
echo ""

echo "🔗 API Documentation (when server running):"
echo "  • http://localhost:8000/docs (Swagger UI)"
echo "  • http://localhost:8000/redoc (ReDoc)"
echo ""

echo "📊 Available CLI Commands:"
echo "  • Autonomy: start, stop"
echo "  • Interaction: chat, task"
echo "  • Learning: learn, read, browse"
echo "  • Status: status, modules, patterns"
echo "  • Testing: simulate, visualize"
echo "  • Other: help, clear, exit"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  SYSTEM REQUIREMENTS                                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✓ Python 3.8 or higher"
echo "✓ 2GB RAM minimum (4GB recommended)"
echo "✓ 500MB disk space for ChromaDB + logs"
echo "✓ OpenAI API key (optional, for LLM features)"
echo ""

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  READY TO START!                                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Run this command to start:"
echo ""
echo "  $PYTHON_CMD AutonomousAI.py"
echo ""
