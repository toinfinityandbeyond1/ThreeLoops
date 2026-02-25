# AUTONOMOUS AI SYSTEM - TECHNICAL SPECIFICATIONS

## Overview

An autonomous learning system that operates continuously in the background, learning from text, URLs, and user interactions through self-supervised prediction. The system is resource-aware, user-aligned, and persistent across sessions.

**Core Philosophy:** Learning emerges from prediction, not from hardcoded rules.

---

## System Architecture

### Three-Loop Memory System

The system maintains three persistent memory tiers that work together:

#### 1. Fast Memory (Immediate)
- **Storage:** In-memory cache + ChromaDB persistence
- **Time horizon:** Recent experiences (current session)
- **Data:** Raw experiences with immediate rewards
- **Purpose:** Quick access to recent patterns
- **Update:** Every interaction, every autonomy cycle

#### 2. Medium Memory (Intermediate)
- **Storage:** Pattern aggregation with ChromaDB
- **Time horizon:** Days to weeks
- **Data:** Aggregated patterns, learned helper code
- **Purpose:** Discover and refine patterns
- **Update:** Once per consolidation cycle

#### 3. Long-Term Memory (Persistent)
- **Storage:** Crystallized modules in ChromaDB
- **Time horizon:** Permanent (across sessions)
- **Data:** Final learned modules with cross-domain links
- **Purpose:** Reusable knowledge base
- **Update:** Once per meta-cycle

### Data Flow

```
User Input / URL / Text
    ↓
Pattern Encoder (universal embedding)
    ↓
Fast Memory (reward + store)
    ↓
[Fast Loop] Prediction + reward comparison
    ↓
[Medium Loop] Pattern aggregation
    ↓
[Long Loop] Module synthesis (meta-learning)
    ↓
Persistent Storage (ChromaDB)
```

---

## Autonomy Loop

The system runs a background loop continuously when not being interacted with by the user.

### Loop Cycle

```python
while running:
    resource_state = monitor_resources()
    user_active = check_user_activity()  # 5s window
    
    if user_active:
        yield_priority()
        sleep(0.1)  # Quick check
        continue
    
    action = scheduler.choose_action(resource_state)
    execute_action(action)
    sleep(adaptive_duration(resource_state))
```

### Four Autonomy Actions

Weighted probabilistic selection with resource-aware adjustment:

| Action | Weight | Function | Condition |
|--------|--------|----------|-----------|
| **Consolidation** | 35% | Replay/compress recent fast memory to medium | Always available |
| **Curiosity** | 25% | Fetch random URL via web_learner | Strain < 0.85 |
| **Prediction** | 20% | Replay past predictions, recompute rewards | Always available |
| **Alignment** | 20% | Execute queued user tasks | Tasks exist |

**Strain-based adjustment:**
```python
adjusted_weights["curiosity"] *= max(0.2, 1.0 - (strain * 0.7))
```

### Adaptive Pacing

```python
sleep_duration = 1.5 + (strain * 2.0)
# Minimum: 1.5s (low load)
# Maximum: 3.5s (high load)
```

---

## Resource Awareness

### Monitoring

**Metrics tracked:**
- CPU usage (%)
- RAM usage (%)
- Disk usage (%)
- Network I/O (KB/s)

**Strain calculation:**
```python
strain = min(1.0, (cpu + ram + disk) / 300.0)
# Range: 0.0 (idle) to 1.0 (saturated)
```

### Autonomy Response

- **Strain 0.0-0.3:** Normal operation, all actions enabled
- **Strain 0.3-0.7:** Curiosity discounted (multiplied by 0.5-0.8)
- **Strain 0.7-0.85:** Curiosity heavily discounted (0.2-0.5)
- **Strain 0.85+:** Web access disabled (curiosity ≈ 0)

---

## User Priority System

### User Activity Detection

```python
mark_user_active()  # Called on every user interaction
last_interaction = time.time()

# Check during autonomy loop
user_active = (time.time() - last_user_interaction) < 5.0
```

### Priority Rules

1. **If user active (< 5s):** Autonomy pauses, yields CPU
2. **If user inactive (≥ 5s):** Autonomy continues
3. **User commands:** Immediately logged as events
4. **Task execution:** Under alignment action, prioritized by user-set priority

---

## Memory Persistence

### Storage Backend

**ChromaDB (Vector Database)**
- Persistent on-disk storage
- Handles all three memory tiers
- Supports semantic search
- Auto-manages vector indexing

**Logging (JSONL format)**
- Raw logs: `/memory/logs/raw/{date}.jsonl` (7-day retention)
- Event logs: `/memory/logs/events/{date}.jsonl` (90-day retention)
- Summaries: `/memory/logs/summaries/summaries.jsonl` (permanent)

### Data Survival

- On restart: immediately loads from ChromaDB
- No in-memory-only critical data
- All decisions logged before execution
- Crash recovery: last valid state

---

## Learning Mechanism

### Universal Pattern Encoder

Converts any input (text, numbers, lists, dicts) to fixed-size vectors (128-dim):

```python
vector = pattern_encoder.encode(data)
# Output: 128-dimensional numpy array
# Invariant to input type
```

### Reward Systems (Stacked)

#### 1. Fast Loop Reward
- **Input:** Prediction vs actual comparison
- **Metric:** Accuracy of next-token prediction
- **Range:** 0.0 to 1.0
- **Used for:** Fast memory priority

#### 2. Meta Reward
- **Input:** Pattern effectiveness (from LLM advisor)
- **Metric:** Semantic coherence and usefulness
- **Range:** 0.0 to 1.0
- **Used for:** Module ranking

#### 3. Autonomous Reward (Composite)
```python
autonomous_reward = (
    0.5 * prediction_accuracy +  # How well we predict
    0.3 * curiosity_score +      # How novel/interesting
    0.2 * consistency_score      # How coherent patterns are
)
```

### Learning Flow

```
Raw Data
    ↓
[Pattern Encoder] → Vector
    ↓
[Fast Loop] Prediction + error signal
    ↓
[Medium Loop] Pattern aggregation + clustering
    ↓
[Long Loop] Module synthesis via meta-learning
    ↓
Knowledge Base
```

---

## Logging Architecture

### Three-Tier Logging

| Tier | Retention | Detail | Purpose |
|------|-----------|--------|---------|
| **Raw** | 7 days | Every event | Debugging, analysis |
| **Event** | 90 days | Important milestones | Performance tracking |
| **Summary** | Permanent | Daily synthesis | Knowledge preservation |

### Log Entry Structure

```json
{
  "timestamp": 1708876543.123,
  "iso": "2026-02-25T10:22:23.123Z",
  "tier": "event",
  "category": "autonomy|learning|chat|task|etc",
  "message": "Human-readable description",
  "data": { "key": "any", "metadata": "here" }
}
```

### Real-time Listeners

```python
log.add_listener(callback)
# Triggered on every log entry
# Used for WebSocket streaming to frontend
```

---

## API Server (FastAPI)

### REST Endpoints

**Status:**
- `GET /health` - Health check
- `GET /status` - Full system status
- `GET /resources` - Current resource snapshot
- `GET /logs?limit=50&tier=event` - Recent logs

**Interaction:**
- `POST /chat` - `{"message": "text"}`
- `POST /task` - `{"data": [1,2,3], "description": "text"}`

**Autonomy:**
- `POST /autonomy/start` - Start loop
- `POST /autonomy/stop` - Stop loop

**Memory:**
- `GET /memory/modules?limit=10` - Recent modules
- `GET /memory/patterns?limit=10` - Top patterns

### WebSocket Endpoints

- `WS /ws/logs` - Real-time log streaming
- `WS /ws/status` - Status updates every 2s

### Response Format

All responses include ISO timestamp:
```json
{
  "data": { ... },
  "timestamp": "2026-02-25T10:22:23.123Z"
}
```

---

## CLI Commands

### Autonomy Control
```
start               Start background learning loop
stop                Stop background learning loop
```

### User Interaction
```
chat <message>      Send message, get response
task <data>         Process structured data
```

### Learning
```
learn <text>        Learn from text input
read <filepath>     Learn from local file
browse <url>        Learn from URL (web_learner)
```

### Inspection
```
status              Show memory/resource/autonomy status
modules [n]         List last n modules
patterns [n]        List top n patterns
```

### Simulation & Testing
```
simulate [days]     Run multi-day simulation
visualize           Plot memory growth, rewards
clear               Clear conversation history
```

### Help & Exit
```
help                Show command list
exit / quit         Exit system
```

---

## Component Classes

### Core Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `AutonomousAI` | Main system orchestrator | AutonomousAI.py |
| `FastMemory` | Fast tier (in-memory + ChromaDB) | AutonomousAI.py |
| `MediumMemory` | Medium tier (pattern aggregation) | AutonomousAI.py |
| `LongTermMemory` | Long-term tier (modules) | AutonomousAI.py |
| `PatternEncoder` | Universal encoder | AutonomousAI.py |
| `PhaseController` | Loop synchronization | AutonomousAI.py |

### Learning Classes

| Class | Purpose |
|-------|---------|
| `RewardSystem` | Fast loop rewards |
| `MetaRewardSystem` | Module ranking |
| `AutonomousRewardSystem` | Composite autonomy reward |
| `OpenAIAdvisor` | Optional LLM acceleration |
| `TextLearner` | Extract patterns from text |
| `WebLearner` | Fetch and learn from URLs |

### Autonomous Classes

| Class | Purpose |
|-------|---------|
| `CognitiveLog` | Tiered logging system |
| `ResourceMonitor` | CPU/RAM/Disk/Network tracking |
| `SelfCore` | Minimal identity model |
| `TaskMemory` | Persistent task queue |
| `AutonomyScheduler` | Action selection |

---

## Configuration & Parameters

### Critical Constants

```python
# Memory
FAST_MEMORY_CACHE_SIZE = 10000
VECTOR_DIM = 128
PATTERN_THRESHOLD = 0.3

# Autonomy
AUTONOMY_SLEEP_MIN = 1.5  # seconds
AUTONOMY_SLEEP_MAX = 3.5
USER_ACTIVITY_WINDOW = 5.0  # seconds
STRAIN_THRESHOLD_WEB = 0.85

# Logging
RAW_RETENTION_DAYS = 7
EVENT_RETENTION_DAYS = 90
MAX_RECENT_LOG_ENTRIES = 200

# Weights (in AutonomyScheduler)
WEIGHT_CONSOLIDATION = 0.35
WEIGHT_CURIOSITY = 0.25
WEIGHT_PREDICTION = 0.20
WEIGHT_ALIGNMENT = 0.20

# Reward Thresholds
CURIOSITY_DISCOUNT_START = 0.3  # Strain level
CURIOSITY_DISCOUNT_HEAVY = 0.7
CURIOSITY_MIN_MULTIPLIER = 0.2
```

---

## Data Structures

### Fast Memory Entry
```python
{
    "id": "uuid",
    "timestamp": 1708876543.123,
    "input": [...],  # Raw data
    "prediction": [...],
    "actual": [...],
    "reward": 0.85,
    "context": {"source": "chat", ...}
}
```

### Pattern (Medium Memory)
```python
{
    "id": "pattern_id",
    "encoding": [...],  # Vector
    "avg_reward": 0.72,
    "usage_count": 15,
    "helper_code": "# Python code",
    "reward_history": [0.6, 0.7, 0.8, ...]
}
```

### Module (Long-Term Memory)
```python
{
    "id": "module_id",
    "encoding": [...],
    "versions": [{"code": "...", "reward": 0.85}],
    "reward_history": [0.6, 0.7, 0.75, ...],
    "lesson_origin": "pattern_123",
    "dependencies": ["other_module_ids"]
}
```

---

## Execution Model

### Session Startup
```
1. Initialize ChromaDB client
2. Load memory from disk (3 tiers)
3. Create reward systems
4. Initialize pattern encoder
5. Start autonomy thread if enabled
6. Enter CLI or API mode
```

### User Interaction Flow
```
User Input → mark_user_active() → log_event()
    ↓
Route to handler (chat/task/learn/etc)
    ↓
Process + generate reward
    ↓
Store in fast memory
    ↓
Log completion event
```

### Autonomy Cycle Flow
```
Check user activity (5s window)
    ↓
If inactive:
  - Monitor resources
  - Select action (weighted)
  - Execute action
  - Log as raw entry
  - Adaptive sleep based on strain
```

---

## Design Principles

### 1. Always-On Learning
- Never explicitly stopped
- Pauseable when user active
- Adapts pacing to load
- No dedicated "training" phase

### 2. Resource Awareness
- No hard quotas
- Self-regulating behavior
- Monitors CPU/RAM/Disk
- Curiosity auto-throttles under load

### 3. User Alignment
- User goals > idle curiosity
- User activity immediately detected
- All interactions logged
- Task execution user-prioritized

### 4. Persistence
- All data on disk
- ChromaDB survivor across restarts
- JSONL logs for inspection
- No critical in-memory state

### 5. Transparency
- Every action logged
- Tiered logging (raw/event/summary)
- WebSocket streaming available
- Full audit trail

---

## Performance Characteristics

### Memory Usage
- **Base:** ~200-300 MB
- **Per 1000 fast entries:** +50 MB
- **Per 100 patterns:** +10 MB
- **Typical:** 300-500 MB

### CPU Usage
- **Idle:** 5-15% (during autonomy)
- **Peak:** Up to 60% (during learning)
- **User interaction:** 10-30%

### Startup Time
- **Cold start (first run):** 2-5 seconds
- **Warm start (resume):** 1-2 seconds

### Latency
- **Chat response:** 100-500ms (depends on LLM)
- **Task processing:** 50-200ms
- **Status query:** <10ms

---

## Assumptions & Limitations

### Current Assumptions
- Single-threaded main loop (background autonomy ok)
- Local-only resource monitoring
- ChromaDB on same machine
- Network available for URLs (but optional)

### Known Limitations
- OpenAI API optional (system works without)
- No distributed/cloud support yet
- No GPU acceleration
- Single user (not multi-tenant)

### Future Extensions
- Distributed memory (federation)
- GPU-accelerated encoding
- Multi-user support
- Advanced meta-learning (RL)

---

## Security & Safety

### User Data
- All stored locally
- No external persistence without permission
- Logs in plaintext (for debugging)

### Resource Limits
- Autonomy loop bounded by sleep duration
- Memory tiers bounded by ChromaDB limits
- Task queue bounded by available memory
- URL fetching rate-limited by curiosity discount

### Safety Measures
- Graceful error handling
- Resource monitoring prevents runaway
- User activity detection prevents "always active"
- Rewards prevent divergent learning

---

## Testing & Validation

### Automated Tests (in test_*.py files)
- System startup/shutdown
- Memory persistence
- Autonomy loop execution
- Logging functionality
- API endpoints

### Manual Verification
```bash
# Verify syntax
python -m py_compile AutonomousAI.py

# Verify startup
python AutonomousAI.py
AI> status
AI> exit

# Verify API (separate terminal)
python -c "from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)"
# curl http://localhost:8000/status
```

---

## Deployment Checklist

- [x] Core system compiles
- [x] All classes defined
- [x] All methods implemented
- [x] CLI commands functional
- [x] Logging operational
- [x] Autonomy loop working
- [x] API server complete
- [x] WebSocket streaming ready
- [x] Memory persistence verified
- [x] Resource monitoring active
- [x] User priority system working

---

## References

**Key Files:**
- `AutonomousAI.py` - Core system (2040 lines)
- `AIServer.py` - Web API backend (500 lines)
- `requirements.txt` - Dependencies

**Key Methods:**
- `AutonomousAI.fast_loop()` - Fast memory learning
- `AutonomousAI.medium_loop()` - Pattern aggregation
- `AutonomousAI.slow_loop()` - Module synthesis
- `AutonomousAI._autonomy_loop()` - Background loop
- `AutonomousAI.chat()` - User interaction

**Architecture:**
- Three-loop memory with persistent storage
- Resource-aware autonomy with user priority
- Reward-driven learning from prediction error
- Tiered logging for transparency

