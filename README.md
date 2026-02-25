# ThreeLoops - Autonomous AI System

An autonomous AI system with a three-loop memory architecture that learns through **self-supervised prediction**. The system can learn language, patterns, and knowledge from any input source without hardcoded rules.

## ⚡ Quick Start

```bash
# Install dependencies (one time)
pip install -r requirements.txt

# Run in interactive mode
python AutonomousAI.py

# Available commands (type in the AI prompt):
# - chat <message>    (talk to the AI)
# - status            (see system status)
# - start             (start autonomy loop)
# - stop              (stop autonomy loop)
# - help              (show all commands)
# - exit              (quit)
```

**For web interface:**
```bash
# Terminal 1: Start API server
python -c "from AutonomousAI import AutonomousAI; from AIServer import run_server; ai = AutonomousAI(); run_server(ai)"

# Terminal 2: Start React frontend
bash create-frontend.sh && cd web-ui && npm install && npm start
# Opens http://localhost:3000
```

See [SETUP_AND_USAGE.md](SETUP_AND_USAGE.md) for detailed instructions.

## 🎯 Core Philosophy

**Learning emerges from prediction, not programming.**

The system doesn't have language rules or domain-specific logic hardcoded. Instead:
- It predicts what comes next
- Compares prediction to reality
- Learns from the difference
- Builds patterns naturally

This works for **anything**: text, numbers, conversations, code, images (future).

## 🧠 Architecture

### Three-Loop Memory System

1. **Fast Memory Loop** - Immediate experiences
   - Stores recent input-output-reward triplets
   - Universal pattern encoding (text, numbers, etc.)
   - Finds similar past experiences
   - **ChromaDB persistence** - Never forgets!

2. **Medium Memory Loop** - Pattern recognition
   - Identifies recurring patterns
   - Tracks pattern performance
   - Retrieves high-reward patterns
   - **Persistent vector storage** for fast retrieval

3. **Slow Memory Loop** - Crystallized modules
   - Stable, proven knowledge modules
   - Cross-domain connections
   - Long-term evolution
   - **Permanent storage** of wisdom

### Autonomous Reward System

The AI generates its own learning signals:
- **Prediction Accuracy**: How well it predicted the outcome
- **Curiosity Reward**: How novel the information is
- **Consistency Reward**: How well it confirms existing knowledge

**No human labeling required** - the system learns by trying to predict and improving from errors.

## ✨ Key Features

- ✅ **Self-Supervised Learning** - Generates own training signal through prediction
- ✅ **Domain-Agnostic** - Same learning mechanism for text, numbers, any data
- ✅ **No Hardcoded Rules** - Language and patterns emerge naturally
- ✅ **Works Without OpenAI** - Fully functional standalone (OpenAI optional for acceleration)
- ✅ **Continuous Learning** - Learns from conversations, documents, web
- ✅ **Persistent Memory** - ChromaDB storage preserves learning across restarts
- ✅ **Phase Coordination** - Ensures all three loops stay synchronized
- ✅ **Pattern Retrieval** - Applies learned knowledge to new situations

## 📖 How It Works

### Self-Supervised Learning Example

```
1. AI sees: "The cat sat on the ___"
2. AI predicts: "mat" (based on learned patterns)
3. Reality reveals: "mat" 
4. Reward: HIGH (correct prediction!)
5. Learning: Strengthens this pattern

Over time, language understanding emerges naturally.
```

### Autonomous Reward Computation

```python
# Reading a document
for sentence in sentences:
    prediction = predict_next(context)
    actual = sentence
    
    # Autonomous reward from prediction accuracy
    reward = compute_similarity(prediction, actual)
    
    # Learn through three loops
    fast_memory.add(context, prediction, actual, reward)
    # Patterns emerge in medium memory
    # Strong patterns crystallize in slow memory
```

## 🚀 Setup

### 1. Install Dependencies

```bash
chmod +x setup.sh
./setup.sh
```

Or manually:
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY='your-api-key-here'
```

To make it permanent, add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo "export OPENAI_API_KEY='your-api-key-here'" >> ~/.bashrc
source ~/.bashrc
```

### 3. Run the System

**Interactive Mode:**
```bash
python3 AutonomousAI.py
```

**Simulation Mode:**
```bash
python3 AutonomousAI.py --simulate 365
```

## 💾 Persistent Memory

The system uses **ChromaDB** for permanent storage - everything learned persists across restarts!

### Memory Storage
- Default Directory: `./ai_memory/`
- Custom Directory: Pass `memory_dir` parameter to `AutonomousAI()`
- Automatic Loading: Learned patterns restore on startup

### What Gets Saved
✅ **Fast Memory** - Recent experiences and their embeddings  
✅ **Medium Memory** - Discovered patterns and their performance  
✅ **Long-Term Memory** - Crystallized knowledge modules  
✅ **Vector Embeddings** - For similarity-based retrieval

### Verify Persistence
```bash
# Learn something
AI> learn The cat sat on the mat

# Exit and restart
AI> exit
python3 AutonomousAI.py

# The pattern is still there!
AI> status
# Will show: "Persistent: X patterns" loaded from disk
```

### Managing Memory
- **View Storage**: `AI> status` shows both active and persistent counts
- **Clear Memory**: Delete `./ai_memory/` directory to start fresh
- **Backup Memory**: Copy `./ai_memory/` directory to preserve learned knowledge

The system continues learning from where it left off - true long-term memory!

## Interactive Commands

### 💬 Conversation (Learns from chat!)
```
AI> chat Hello, how does learning work?
AI> chat What is machine learning?
```
The AI learns from every conversation - no external labeling needed!

### 📚 Learn from Text
```
AI> learn Machine learning is awesome. Neural networks learn patterns.
AI> read document.txt
AI> browse https://en.wikipedia.org/wiki/Machine_learning
```

### 🔧 Process Tasks
```
AI> task [5,2,8,1,9] sort these numbers  
AI> task analyze this pattern
```

### 📊 Monitor Learning
```
AI> status           # Current system state
AI> modules 10       # Top learned modules
AI> patterns 10      # Pattern recognition stats
```

### 🎮 Other Commands
```
AI> simulate 7       # Run 7-day autonomous learning
AI> visualize        # Show learning progress charts
AI> clear            # Reset conversation context
AI> help             # Full command list
```

## Usage Examples

### Example 1: Autonomous Text Learning

```
AI> learn The quick brown fox jumps over the lazy dog. Foxes are clever animals.

Learning from text...
✓ Learned 2 sentence patterns
  Average reward: 0.73
  
The AI predicted the second sentence based on the first and learned from the accuracy!
```

### Example 2: Conversation That Actually Learns

```
AI> chat Hello

AI: Hello! I'm learning to converse. How can I help you?

AI> chat What is machine learning?

AI: That's an interesting question about 'What is machine learning?'...

AI> learn Machine learning is when computers learn from data without explicit programming.

✓ Learned 1 patterns

AI> chat What is machine learning?

AI: Based on learned patterns: Machine learning is when computers learn from data...

# It remembered and improved!
```

### Example 3: Web Learning

```
AI> browse https://simple.wikipedia.org/wiki/Artificial_intelligence

Fetching: https://simple.wikipedia.org/wiki/Artificial_intelligence
✓ Learned from URL: 487 patterns

The AI read the page, predicted next sentences, and learned from accuracy!
```

### Example 4: See What It Learned

```
AI> patterns 5

============================================================
TOP MEDIUM MEMORY PATTERNS
============================================================

1. Pattern: wiki_learning
   Avg Reward: 0.85
   Usage: 47 times
   Code: # Pattern: 'learning' appears 47 times in wiki

2. Pattern: chat_hello
   Avg Reward: 0.78
   Usage: 12 times
   Code: # User: Hello
         # Response: Hello! I'm learning...
```

## Phase Coordination

The system ensures all three loops work together for **every learning event**:

```
Input → PREDICT → Observe Reality → Compute Reward
         ↓              ↓                ↓
    Fast Loop → Medium Loop → Slow Loop
         ↓              ↓                ↓
    Store exp.  → Find pattern → Build module
         ↓              ↓                ↓
    Phase 1 ✓    → Phase 2 ✓     → Phase 3 ✓
```

**All phases must complete before next input** - ensures consistent learning.

## 🔬 Architecture Details

### Universal Pattern Encoding
```python
PatternEncoder:
  - Converts ANY data to vector representation
  - Text → word frequency vectors
  - Numbers → normalized arrays
  - Works for lists, dicts, strings, etc.
  - Enables similarity search across all data types
```

### Autonomous Reward Signals
```python
AutonomousRewardSystem:
  1. Prediction Reward (50%)
     - How accurate was the prediction?
     - Uses cosine similarity
  
  2. Curiosity Reward (30%)
     - How novel is this information?
     - Sweet spot: somewhat novel but learnable
  
  3. Consistency Reward (20%)
     - Does this confirm existing patterns?
     - Builds confidence in knowledge
```

### Memory Systems
- **FastMemory**: Similarity search, pattern matching, recent experiences
- **MediumMemory**: Pattern ranking, usage tracking, reward history
- **LongTermMemory**: Module retrieval, cross-domain linking, evolution

### Learning From Any Source
- **TextLearner**: Prediction-based learning from documents
- **WebLearner**: Fetch and learn from URLs
- **Conversation**: Learn from chat interactions
- **Tasks**: Learn from structured data

### OpenAI Integration (Optional)
OpenAI acts as an **advisor/validator**, not the brain:
- Suggests better responses when confidence is low
- Validates AI's self-assessment
- Accelerates learning but isn't required
- System works fully without it

## 🎯 What Makes This Different

### Traditional AI
```
Human labels data → AI learns from labels
```

### This System
```
AI predicts → Reality teaches → AI learns
```

**The difference**: No human in the loop needed. The AI generates its own training signal through prediction.

### Emergent Intelligence
```
Input many documents → AI predicts sentences → Patterns emerge → Language understanding develops

NOT: Hardcode grammar rules → Parse text
BUT: Try to predict → Learn from errors → Understanding emerges
```

## 🆘 Troubleshooting

### "No module named 'sklearn'"
Install dependencies:
```bash
pip install -r requirements.txt
```

### "OPENAI_API_KEY not found" - **This is OK!**
The system works fully without OpenAI. The warning just means optional acceleration features won't be available.

To enable OpenAI advisor (optional):
```bash
export OPENAI_API_KEY='your-key-here'
```

### Visualization windows don't appear
In headless environments, set:
```bash
export MPLBACKEND=Agg  # Save plots instead of displaying
```

### Low conversation quality initially
**This is expected!** The AI starts with no language knowledge. Feed it some text:
```
AI> read book.txt
AI> browse https://simple.wikipedia.org/wiki/Your_topic
AI> learn [your explanations here]
```

## 🔮 Future Enhancements

- [ ] Persistent storage (save/load learned patterns)
- [ ] Advanced reasoning (chain-of-thought)
- [ ] Multi-modal learning (images, audio)
- [ ] Web scraping with better parsing
- [ ] Active learning (AI asks clarifying questions)
- [ ] Meta-learning about reward calibration
- [ ] Distributed learning across multiple instances
- [ ] Custom reward functions
- [ ] Knowledge graph visualization
- [ ] Attention mechanisms

## 🧪 Running the Demo

```bash
python3 demo_autonomous_learning.py
```

This shows:
- Text learning through prediction
- Conversation learning
- Pattern emergence
- Autonomous reward signals
- All without OpenAI API!

## License

MIT License - See LICENSE file for details

## Contributing

Contributions welcome! Please submit pull requests or open issues.
