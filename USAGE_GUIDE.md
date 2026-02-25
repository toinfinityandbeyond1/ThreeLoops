# USAGE GUIDE

## Quick Start (30 seconds)

```bash
python AutonomousAI.py
AI> help
AI> status
AI> exit
```

---

## Installation

```bash
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."  # Optional, for LLM features
```

---

## Three Ways to Run

### 1. CLI Only (Simplest)
```bash
python AutonomousAI.py
```

Then use commands:
```
AI> chat Hello world
AI> status
AI> start              (start autonomy)
AI> stop               (stop autonomy)
AI> help               (see all commands)
```

### 2. With Web API
```bash
# Terminal 1
python -c "from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)"
```

Server runs on `http://localhost:8000`

Endpoints:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"message": "Hello"}'
curl -X POST http://localhost:8000/autonomy/start
```

API docs: `http://localhost:8000/docs`

### 3. Full Stack (Web API + React UI)

**Terminal 1 (API Server):**
```bash
python -c "from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)"
```

**Terminal 2 (React Frontend):**
```bash
bash create-frontend.sh
cd web-ui
npm install
npm start
```

Opens `http://localhost:3000`

---

## Available Commands

### Autonomy Control
```
start               Start background learning loop
stop                Stop background learning loop
```

### User Interaction
```
chat <message>      Chat with AI
task <data>         Process data or task
                    Example: task [1,5,3,2,4] sort these
```

### Learning
```
learn <text>        Learn from text input
read <file>         Learn from local file
browse <url>        Learn from URL
```

### Inspect System
```
status              Show memory/resource/autonomy status
modules [n]         List last n modules (default 10)
patterns [n]        List top n patterns (default 10)
```

### Testing & Visualization
```
simulate [days]     Run n-day simulation
visualize           Plot memory growth and rewards
clear               Clear conversation history
```

### Help & Exit
```
help                Show this help
exit / quit         Exit
```

---

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="sk-..."          # OpenAI API key (optional)
export AI_MEMORY_DIR="./memory"         # Memory storage location
```

### System Parameters

Edit in `AutonomousAI.__init__()`:
- Memory cache sizes
- Autonomy weights (consolidation/curiosity/prediction/alignment)
- Log retention periods
- Strain thresholds

---

## API Reference

### REST Endpoints

**Status:**
```
GET /health                              Health check
GET /status                              Full system status
GET /resources                           Resource snapshot
GET /logs?limit=50&tier=event            Recent logs
```

**Interaction:**
```
POST /chat                               Send message
     {"message": "your message"}

POST /task                               Process task
     {"data": [1,2,3], "description": "text"}
```

**Autonomy:**
```
POST /autonomy/start                     Start autonomy
POST /autonomy/stop                      Stop autonomy
```

**Memory:**
```
GET /memory/modules?limit=10             Recent modules
GET /memory/patterns?limit=10            Top patterns
```

### WebSocket Endpoints

```
WS /ws/logs                              Real-time log stream
WS /ws/status                            Status updates (2s refresh)
```

### Response Format
```json
{
  "data": { ... },
  "timestamp": "2026-02-25T10:22:23.123Z"
}
```

---

## Example Workflows

### 1. Interactive Learning Session
```
AI> learn The mitochondria is the powerhouse of the cell
Learning from text... ✓ Learned 3 patterns

AI> chat What is the mitochondria?
AI Response: [response based on learning]
```

### 2. Run a Simulation
```
AI> simulate 7
[Running 7-day simulation...]
[Day 1] 42 fast memory entries
[Day 2] 89 fast memory entries
...
✓ Simulation complete

AI> visualize
[Shows memory growth and reward charts]
```

### 3. Web Server + API
```bash
# Terminal 1
python -c "from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)"

# Terminal 2
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about machine learning"}'
```

### 4. Enable Autonomy
```
AI> start
✓ Autonomy loop started

AI> status
[shows autonomy_running: true]

[AI learns in background while you do other things]

AI> stop
✓ Autonomy loop stopped
```

---

## Troubleshooting

### Python Import Errors
```bash
pip install -r requirements.txt --upgrade
```

### Port 8000 Already In Use
```bash
lsof -i :8000           # Find what's using it
kill -9 <PID>           # Kill it
# Or use different port in AIServer.py
```

### OpenAI API Issues
```bash
echo $OPENAI_API_KEY    # Verify it's set

# Test connectivity
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### React App Won't Start
```bash
cd web-ui
rm -rf node_modules package-lock.json
npm install
npm start
```

### Memory Usage Too High
```
AI> status
[Check memory counts]

AI> clear              # Clear conversation history
# Reduce simulation size: simulate 3 (instead of 7)
```

---

## Performance Tips

### For CPU-Heavy Tasks
- Run shorter simulations: `simulate 3` instead of `simulate 30`
- Let autonomy run during idle time
- Disable visualization if charts are slow

### For Memory Safety
- Monitor with `status` command regularly
- Clear history with `clear` if needed
- Scale back simulation size if strain > 0.8

### For Web Learning
- Browse URLs during low-usage periods
- Use local files with `read` when possible
- System auto-throttles when under load

---

## File Locations

```
./memory/                              # All data (ChromaDB + logs)
./memory/logs/raw/                     # Raw logs (7 days)
./memory/logs/events/                  # Event logs (90 days)
./memory/logs/summaries/               # Summaries (permanent)
```

---

## Architecture Overview

**See TECHNICAL_SPECS.md for detailed architecture.**

Quick summary:
- **Three-Loop Memory:** Fast (recent) → Medium (patterns) → Long-Term (modules)
- **Autonomy Loop:** Background thread with 4 actions (consolidation/curiosity/prediction/alignment)
- **Resource-Aware:** Monitors CPU/RAM/Disk, throttles based on strain
- **User-Aligned:** Yields to user interaction automatically
- **Persistent:** All data survives restarts via ChromaDB

---

## Advanced Usage

### Custom Autonomy Weights
Edit `AutonomyScheduler()` in AutonomousAI.py:
```python
self.weights = {
    "consolidation": 0.35,  # Increase for more memory work
    "curiosity": 0.25,      # Increase for more web learning
    "prediction": 0.20,
    "alignment": 0.20       # Increase for more task execution
}
```

### Add Custom Command
Edit `run_interactive_mode()` in AutonomousAI.py:
```python
elif command == "mycommand":
    ai.mark_user_active()
    result = ai.my_method()
    print(result)
```

### Add API Endpoint
Edit `AIServer.py`:
```python
@app.get("/my-endpoint")
async def my_endpoint():
    return {"result": ai.my_method()}
```

---

## Support & Documentation

**Technical Details:** See TECHNICAL_SPECS.md  
**What Was Built:** See COMPLETION_REPORT.md  
**Quick Answers:** See README.md  

---

## Getting Help

1. **Command not working?** → Type `help` in CLI
2. **API endpoint issue?** → Check `http://localhost:8000/docs` (when server running)
3. **Want to understand how it works?** → Read TECHNICAL_SPECS.md
4. **System acting weird?** → Check `status` command

---

## Next Steps

- **Try it now:** `python AutonomousAI.py`
- **Explore commands:** Type `help` then try a few
- **Enable autonomy:** Type `start` then check `status` every few seconds
- **Build the web UI:** Run `bash create-frontend.sh` for interactive React dashboard
