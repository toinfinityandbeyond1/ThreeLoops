import random
import hashlib
import numpy as np
import time
import matplotlib.pyplot as plt
import networkx as nx
import os
import json
from openai import OpenAI
import sys
import re
import requests
from bs4 import BeautifulSoup
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import chromadb
from chromadb.config import Settings
from datetime import datetime, timedelta
from threading import Thread, Lock
from collections import deque
import psutil

# -----------------------------
# Cognitive Logging (raw/events/summaries)
# -----------------------------

class CognitiveLog:
  """Tiered log with retention and real-time listeners."""

  def __init__(self, base_dir, raw_retention_days=7, event_retention_days=90, max_recent=200):
    self.base_dir = base_dir
    self.raw_retention_days = raw_retention_days
    self.event_retention_days = event_retention_days
    self.max_recent = max_recent

    self.raw_dir = os.path.join(base_dir, "logs", "raw")
    self.event_dir = os.path.join(base_dir, "logs", "events")
    self.summary_dir = os.path.join(base_dir, "logs", "summaries")

    os.makedirs(self.raw_dir, exist_ok=True)
    os.makedirs(self.event_dir, exist_ok=True)
    os.makedirs(self.summary_dir, exist_ok=True)

    self.recent_raw = deque(maxlen=max_recent)
    self.recent_events = deque(maxlen=max_recent)
    self.listeners = []
    self.lock = Lock()
    self.last_cleanup = time.time()

  def add_listener(self, listener):
    self.listeners.append(listener)

  def _write_jsonl(self, path, record):
    with open(path, "a", encoding="utf-8") as f:
      f.write(json.dumps(record) + "\n")

  def _log(self, tier, message, category="general", data=None):
    now = datetime.utcnow()
    record = {
      "timestamp": now.timestamp(),
      "iso": now.isoformat() + "Z",
      "tier": tier,
      "category": category,
      "message": message,
      "data": data or {}
    }

    date_key = now.strftime("%Y-%m-%d")
    if tier == "raw":
      path = os.path.join(self.raw_dir, f"{date_key}.jsonl")
      self._write_jsonl(path, record)
      with self.lock:
        self.recent_raw.append(record)
    elif tier == "event":
      path = os.path.join(self.event_dir, f"{date_key}.jsonl")
      self._write_jsonl(path, record)
      with self.lock:
        self.recent_events.append(record)
    elif tier == "summary":
      path = os.path.join(self.summary_dir, "summaries.jsonl")
      self._write_jsonl(path, record)

    for listener in self.listeners:
      listener(record)

    if time.time() - self.last_cleanup > 3600:
      self._cleanup()
      self.last_cleanup = time.time()

  def log_raw(self, message, category="general", data=None):
    self._log("raw", message, category, data)

  def log_event(self, message, category="event", data=None):
    self._log("event", message, category, data)

  def log_summary(self, message, data=None):
    self._log("summary", message, "summary", data)

  def get_recent_raw(self, limit=50):
    with self.lock:
      return list(self.recent_raw)[-limit:]

  def get_recent_events(self, limit=50):
    with self.lock:
      return list(self.recent_events)[-limit:]

  def _cleanup(self):
    now = datetime.utcnow()

    def clean_dir(dir_path, retention_days):
      for name in os.listdir(dir_path):
        if not name.endswith(".jsonl"):
          continue
        try:
          date_str = name.replace(".jsonl", "")
          day = datetime.strptime(date_str, "%Y-%m-%d")
          if now - day > timedelta(days=retention_days):
            os.remove(os.path.join(dir_path, name))
        except Exception:
          continue

    clean_dir(self.raw_dir, self.raw_retention_days)
    clean_dir(self.event_dir, self.event_retention_days)

# -----------------------------
# Resource Awareness
# -----------------------------

class ResourceMonitor:
  """Tracks resource usage so autonomy can self-regulate."""

  def __init__(self):
    self.last_net = psutil.net_io_counters()
    self.last_time = time.time()

  def snapshot(self):
    now = time.time()
    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    net = psutil.net_io_counters()
    elapsed = max(1e-6, now - self.last_time)
    net_kbps = ((net.bytes_sent - self.last_net.bytes_sent) + (net.bytes_recv - self.last_net.bytes_recv)) / 1024 / elapsed

    self.last_net = net
    self.last_time = now

    strain = min(1.0, (cpu + mem + disk) / 300.0)

    return {
      "cpu_percent": cpu,
      "memory_percent": mem,
      "disk_percent": disk,
      "net_kbps": net_kbps,
      "strain": strain
    }

# -----------------------------
# Minimal Self Model (Assistant-aligned)
# -----------------------------

class SelfCore:
  """Minimal, human-aligned self model for an assistant."""

  def __init__(self, owner="user"):
    self.identity = {
      "role": "learning assistant",
      "owner": owner,
      "priority_rule": "User goals override idle curiosity"
    }
    self.drives = ["curiosity", "accuracy", "coherence", "helpfulness"]

  def summary(self):
    return {
      "role": self.identity["role"],
      "owner": self.identity["owner"],
      "priority_rule": self.identity["priority_rule"],
      "drives": self.drives
    }

# -----------------------------
# Task Memory (minimal persistence)
# -----------------------------

class TaskMemory:
  """Stores user tasks with minimal persistence."""

  def __init__(self, chroma_client, log):
    self.collection = chroma_client.get_or_create_collection(
      name="tasks",
      metadata={"description": "Minimal task memory"}
    )
    self.log = log
    self.pending = []
    self.completed = 0
    self._load_pending()

  def _load_pending(self):
    try:
      results = self.collection.get(include=["metadatas", "documents"])
      if results['ids']:
        for task_id, doc, metadata in zip(results['ids'], results['documents'], results['metadatas']):
          if metadata.get("status") == "pending":
            self.pending.append({
              "id": task_id,
              "description": doc,
              "priority": float(metadata.get("priority", 0.5)),
              "created": float(metadata.get("created", time.time()))
            })
    except Exception:
      pass

  def add_task(self, description, priority=0.5):
    task_id = f"task_{int(time.time())}_{random.randint(1000, 9999)}"
    created = time.time()
    self.pending.append({
      "id": task_id,
      "description": description,
      "priority": priority,
      "created": created
    })
    self.collection.add(
      ids=[task_id],
      documents=[description],
      metadatas=[{
        "status": "pending",
        "priority": str(priority),
        "created": str(created)
      }]
    )
    self.log.log_event("Task added", "task", {"id": task_id, "description": description})
    return task_id

  def next_task(self):
    if not self.pending:
      return None
    self.pending.sort(key=lambda t: (-t["priority"], t["created"]))
    return self.pending.pop(0)

  def complete_task(self, task_id, result=None):
    self.completed += 1
    try:
      metadata = self.collection.get(ids=[task_id], include=["metadatas"])['metadatas'][0]
      metadata["status"] = "completed"
      metadata["completed"] = str(time.time())
      if result is not None:
        metadata["result"] = str(result)
      self.collection.update(ids=[task_id], metadatas=[metadata])
    except Exception:
      pass
    self.log.log_event("Task completed", "task", {"id": task_id})

  def count(self):
    return len(self.pending)

# -----------------------------
# Autonomy Scheduler (macro-level)
# -----------------------------

class AutonomyScheduler:
  """Selects high-level activity based on weights and resource strain."""

  def __init__(self, weights=None):
    self.weights = weights or {
      "consolidation": 0.35,
      "curiosity": 0.25,
      "prediction": 0.20,
      "alignment": 0.20
    }

  def choose_action(self, resource_state, user_active):
    if user_active:
      return None

    strain = resource_state.get("strain", 0.0)
    adjusted = dict(self.weights)
    adjusted["curiosity"] *= max(0.2, 1.0 - (strain * 0.7))

    total = sum(adjusted.values())
    if total <= 0:
      return None

    actions = list(adjusted.keys())
    weights = [w / total for w in adjusted.values()]
    return random.choices(actions, weights=weights, k=1)[0]

# -----------------------------
# Universal Pattern Encoding
# -----------------------------

class PatternEncoder:
  """Encodes any input type into a universal vector representation"""
  
  def __init__(self, embedding_dim=128):
    self.embedding_dim = embedding_dim
    self.vocab = {}  # word -> id mapping
    self.vocab_size = 0
  
  def encode(self, data):
    """Convert any data type to vector representation"""
    if isinstance(data, str):
      return self.encode_text(data)
    elif isinstance(data, (list, tuple)):
      return self.encode_sequence(data)
    elif isinstance(data, (int, float)):
      return np.array([data])
    elif isinstance(data, np.ndarray):
      return data.flatten()
    elif isinstance(data, dict):
      return self.encode_dict(data)
    else:
      # Fallback: convert to string and encode
      return self.encode_text(str(data))
  
  def encode_text(self, text):
    """Simple text encoding using word frequencies"""
    # Tokenize
    words = re.findall(r'\w+', text.lower())
    
    # Update vocabulary
    for word in words:
      if word not in self.vocab:
        self.vocab[word] = self.vocab_size
        self.vocab_size += 1
    
    # Create bag-of-words vector (fixed size)
    vector = np.zeros(self.embedding_dim)
    word_counts = Counter(words)
    
    for word, count in word_counts.items():
      idx = self.vocab[word] % self.embedding_dim  # Hash to fixed size
      vector[idx] += count
    
    # Normalize
    norm = np.linalg.norm(vector)
    if norm > 0:
      vector = vector / norm
    
    return vector
  
  def encode_sequence(self, seq):
    """Encode list/tuple as vector"""
    try:
      # Try numeric conversion
      arr = np.array(seq, dtype=float)
      # Pad or truncate to embedding_dim
      if len(arr) < self.embedding_dim:
        arr = np.pad(arr, (0, self.embedding_dim - len(arr)))
      else:
        arr = arr[:self.embedding_dim]
      return arr
    except:
      # Mixed types - encode as text
      return self.encode_text(str(seq))
  
  def encode_dict(self, d):
    """Encode dictionary"""
    return self.encode_text(json.dumps(d))
  
  def compute_similarity(self, vec1, vec2):
    """Compute cosine similarity between vectors"""
    vec1 = vec1.reshape(1, -1)
    vec2 = vec2.reshape(1, -1)
    return cosine_similarity(vec1, vec2)[0][0]

# -----------------------------
# Memory Classes (ChromaDB-backed)
# -----------------------------

class FastMemory:
  """Fast memory with ChromaDB persistence and in-memory cache"""
  
  def __init__(self, chroma_client, max_cache=1000):
    self.collection = chroma_client.get_or_create_collection(
      name="fast_memory",
      metadata={"description": "Recent experiences and predictions"}
    )
    self.max_cache = max_cache
    self.cache = []  # Small in-memory cache for speed
    self._load_cache()
  
  def _load_cache(self):
    """Load recent entries into cache"""
    try:
      results = self.collection.get(
        limit=self.max_cache,
        include=["documents", "metadatas", "embeddings"]
      )
      if results['ids']:
        for i in range(len(results['ids'])):
          self.cache.append({
            "input": results['documents'][i],
            "reward": results['metadatas'][i].get('reward', 0.5),
            "embedding": np.array(results['embeddings'][i]) if results['embeddings'] else None,
            "prediction": results['metadatas'][i].get('prediction', ''),
            "actual": results['metadatas'][i].get('actual', ''),
            "timestamp": results['metadatas'][i].get('timestamp', time.time()),
            "context": json.loads(results['metadatas'][i].get('context', '{}'))
          })
    except Exception as e:
      print(f"[FastMemory] Cache load warning: {e}")
  
  @property
  def entries(self):
    """Backward compatibility - return cache as entries"""
    return self.cache
  
  def add(self, input_data, prediction, actual, reward, input_embedding=None, context=None):
    """Store experience with persistent storage"""
    entry_id = f"fast_{int(time.time() * 1000000)}"
    
    # Prepare data
    doc = str(input_data)
    metadata = {
      "prediction": str(prediction)[:500],  # Truncate for storage
      "actual": str(actual)[:500],
      "reward": float(reward),
      "timestamp": time.time(),
      "context": json.dumps(context or {})
    }
    
    # Store in ChromaDB
    if input_embedding is not None:
      embedding = input_embedding.tolist() if isinstance(input_embedding, np.ndarray) else input_embedding
      self.collection.add(
        ids=[entry_id],
        documents=[doc],
        embeddings=[embedding],
        metadatas=[metadata]
      )
    else:
      # No embedding - store without it
      self.collection.add(
        ids=[entry_id],
        documents=[doc],
        metadatas=[metadata]
      )
    
    # Update cache
    entry = {
      "input": input_data,
      "prediction": prediction,
      "actual": actual,
      "reward": reward,
      "timestamp": time.time(),
      "embedding": input_embedding,
      "context": context or {}
    }
    self.cache.append(entry)
    if len(self.cache) > self.max_cache:
      self.cache.pop(0)
  
  def find_similar(self, embedding, n=5):
    """Find similar patterns using ChromaDB vector search"""
    if embedding is None:
      return []
    
    try:
      embedding_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
      
      results = self.collection.query(
        query_embeddings=[embedding_list],
        n_results=min(n, 100),
        include=["documents", "metadatas", "embeddings", "distances"]
      )
      
      if not results['ids'][0]:
        return []
      
      # Convert to expected format
      similar = []
      for i in range(len(results['ids'][0])):
        # ChromaDB returns distances, convert to similarity (1 - normalized_distance)
        distance = results['distances'][0][i]
        similarity = 1.0 / (1.0 + distance)  # Convert L2 distance to similarity
        
        entry = {
          "input": results['documents'][0][i],
          "prediction": results['metadatas'][0][i].get('prediction', ''),
          "actual": results['metadatas'][0][i].get('actual', ''),
          "reward": results['metadatas'][0][i].get('reward', 0.5),
          "embedding": np.array(results['embeddings'][0][i]) if results.get('embeddings') else None,
          "timestamp": results['metadatas'][0][i].get('timestamp', 0),
          "context": json.loads(results['metadatas'][0][i].get('context', '{}'))
        }
        similar.append((similarity, entry))
      
      return similar
      
    except Exception as e:
      print(f"[FastMemory] Similarity search error: {e}")
      # Fallback to cache-based search
      similarities = []
      for entry in self.cache:
        if entry.get('embedding') is not None:
          sim = cosine_similarity(
            embedding.reshape(1, -1),
            entry['embedding'].reshape(1, -1)
          )[0][0]
          similarities.append((sim, entry))
      similarities.sort(reverse=True, key=lambda x: x[0])
      return similarities[:n]

class MediumMemory:
  """Medium memory with ChromaDB persistence for pattern recognition"""
  
  def __init__(self, chroma_client):
    self.collection = chroma_client.get_or_create_collection(
      name="medium_memory",
      metadata={"description": "Recognized patterns and routines"}
    )
    self.patterns = {}  # In-memory cache
    self._load_patterns()
  
  def _load_patterns(self):
    """Load patterns into memory cache"""
    try:
      results = self.collection.get(
        include=["documents", "metadatas", "embeddings"]
      )
      if results['ids']:
        for i, pattern_id in enumerate(results['ids']):
          self.patterns[pattern_id] = {
            "helper_code": results['documents'][i],
            "reward_history": json.loads(results['metadatas'][i].get('reward_history', '[]')),
            "usage_count": results['metadatas'][i].get('usage_count', 1),
            "embedding": np.array(results['embeddings'][i]) if results.get('embeddings') and results['embeddings'][i] else None,
            "avg_reward": results['metadatas'][i].get('avg_reward', 0.5)
          }
    except Exception as e:
      print(f"[MediumMemory] Load warning: {e}")

  def add_pattern(self, pattern_id, helper_code, reward, embedding=None):
    """Store recognized pattern with embedding for retrieval"""
    
    # Check if pattern exists
    if pattern_id in self.patterns:
      # Update existing
      self.patterns[pattern_id]["reward_history"].append(reward)
      self.patterns[pattern_id]["usage_count"] += 1
      self.patterns[pattern_id]["avg_reward"] = np.mean(self.patterns[pattern_id]["reward_history"])
      
      # Update in ChromaDB
      metadata = {
        "reward_history": json.dumps(self.patterns[pattern_id]["reward_history"]),
        "usage_count": self.patterns[pattern_id]["usage_count"],
        "avg_reward": float(self.patterns[pattern_id]["avg_reward"])
      }
      
      try:
        self.collection.delete(ids=[pattern_id])
        if embedding is not None:
          emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
          self.collection.add(
            ids=[pattern_id],
            documents=[helper_code],
            embeddings=[emb_list],
            metadatas=[metadata]
          )
        else:
          self.collection.add(
            ids=[pattern_id],
            documents=[helper_code],
            metadatas=[metadata]
          )
      except Exception as e:
        print(f"[MediumMemory] Update error: {e}")
    else:
      # New pattern
      self.patterns[pattern_id] = {
        "helper_code": helper_code,
        "reward_history": [reward],
        "usage_count": 1,
        "embedding": embedding,
        "avg_reward": reward
      }
      
      # Store in ChromaDB
      metadata = {
        "reward_history": json.dumps([reward]),
        "usage_count": 1,
        "avg_reward": float(reward)
      }
      
      try:
        if embedding is not None:
          emb_list = embedding.tolist() if isinstance(embedding, np.ndarray) else embedding
          self.collection.add(
            ids=[pattern_id],
            documents=[helper_code],
            embeddings=[emb_list],
            metadatas=[metadata]
          )
        else:
          self.collection.add(
            ids=[pattern_id],
            documents=[helper_code],
            metadatas=[metadata]
          )
      except Exception as e:
        print(f"[MediumMemory] Add error: {e}")
  
  def find_best_patterns(self, threshold=0.5, limit=10):
    """Retrieve high-performing patterns"""
    good_patterns = [
      (pid, pdata) for pid, pdata in self.patterns.items()
      if pdata["avg_reward"] >= threshold
    ]
    good_patterns.sort(key=lambda x: x[1]["avg_reward"], reverse=True)
    return good_patterns[:limit]

class LongTermMemory:
  """Long-term memory with ChromaDB persistence for evolved modules"""
  
  def __init__(self, chroma_client):
    self.collection = chroma_client.get_or_create_collection(
      name="long_term_memory",
      metadata={"description": "Crystallized knowledge modules"}
    )
    self.modules = {}  # In-memory cache
    self._load_modules()
  
  def _load_modules(self):
    """Load modules into memory cache"""
    try:
      results = self.collection.get(
        include=["documents", "metadatas", "embeddings"]
      )
      if results['ids']:
        for i, module_id in enumerate(results['ids']):
          self.modules[module_id] = {
            "code_ast": results['documents'][i],
            "embedding": np.array(results['embeddings'][i]) if results.get('embeddings') and results['embeddings'][i] else None,
            "lesson_origin": results['metadatas'][i].get('lesson_origin', 'unknown'),
            "versions": json.loads(results['metadatas'][i].get('versions', '[]')),
            "reward_history": json.loads(results['metadatas'][i].get('reward_history', '[]')),
            "cross_domain_links": json.loads(results['metadatas'][i].get('cross_domain_links', '[]')),
            "avg_reward": results['metadatas'][i].get('avg_reward', 0.5),
            "usage_count": results['metadatas'][i].get('usage_count', 1)
          }
    except Exception as e:
      print(f"[LongTermMemory] Load warning: {e}")

  def add_module(self, module_id, code_ast, embedding, lesson_origin, version, reward, cross_links=None):
    """Add or update a long-term module"""
    
    if module_id in self.modules:
      # Update existing
      self.modules[module_id]["versions"].append(version)
      self.modules[module_id]["reward_history"].append(reward)
      self.modules[module_id]["avg_reward"] = np.mean(self.modules[module_id]["reward_history"])
      self.modules[module_id]["usage_count"] += 1
      if cross_links:
        self.modules[module_id]["cross_domain_links"].extend(cross_links)
      
      # Update in ChromaDB
      metadata = {
        "lesson_origin": lesson_origin,
        "versions": json.dumps(self.modules[module_id]["versions"]),
        "reward_history": json.dumps(self.modules[module_id]["reward_history"]),
        "cross_domain_links": json.dumps(self.modules[module_id]["cross_domain_links"]),
        "avg_reward": float(self.modules[module_id]["avg_reward"]),
        "usage_count": self.modules[module_id]["usage_count"]
      }
      
      try:
        self.collection.delete(ids=[module_id])
        if embedding is not None:
          emb_list = embedding if isinstance(embedding, list) else embedding.tolist()
          self.collection.add(
            ids=[module_id],
            documents=[code_ast],
            embeddings=[emb_list],
            metadatas=[metadata]
          )
        else:
          self.collection.add(
            ids=[module_id],
            documents=[code_ast],
            metadatas=[metadata]
          )
      except Exception as e:
        print(f"[LongTermMemory] Update error: {e}")
    else:
      # New module
      self.modules[module_id] = {
        "code_ast": code_ast,
        "embedding": embedding,
        "lesson_origin": lesson_origin,
        "versions": [version],
        "reward_history": [reward],
        "cross_domain_links": cross_links or [],
        "avg_reward": reward,
        "usage_count": 1
      }
      
      # Store in ChromaDB
      metadata = {
        "lesson_origin": lesson_origin,
        "versions": json.dumps([version]),
        "reward_history": json.dumps([reward]),
        "cross_domain_links": json.dumps(cross_links or []),
        "avg_reward": float(reward),
        "usage_count": 1
      }
      
      try:
        if embedding is not None:
          emb_list = embedding if isinstance(embedding, list) else embedding.tolist()
          self.collection.add(
            ids=[module_id],
            documents=[code_ast],
            embeddings=[emb_list],
            metadatas=[metadata]
          )
        else:
          self.collection.add(
            ids=[module_id],
            documents=[code_ast],
            metadatas=[metadata]
          )
      except Exception as e:
        print(f"[LongTermMemory] Add error: {e}")
  
  def find_relevant_modules(self, embedding, threshold=0.3, limit=5):
    """Find modules relevant to current input"""
    if embedding is None:
      return []
    
    try:
      emb_list = embedding if isinstance(embedding, list) else embedding.tolist()
      
      results = self.collection.query(
        query_embeddings=[emb_list],
        n_results=min(limit * 2, 50),
        include=["documents", "metadatas", "embeddings", "distances"]
      )
      
      if not results['ids'][0]:
        return []
      
      relevant = []
      for i in range(len(results['ids'][0])):
        module_id = results['ids'][0][i]
        distance = results['distances'][0][i]
        similarity = 1.0 / (1.0 + distance)
        
        if similarity >= threshold:
          module_data = self.modules.get(module_id, {})
          avg_reward = module_data.get('avg_reward', 0.5)
          score = similarity * 0.6 + avg_reward * 0.4
          relevant.append((score, module_id, module_data))
      
      relevant.sort(reverse=True, key=lambda x: x[0])
      return relevant[:limit]
      
    except Exception as e:
      print(f"[LongTermMemory] Search error: {e}")
      return []

# -----------------------------
# Autonomous Reward System
# -----------------------------
class AutonomousRewardSystem:
  """Computes rewards from multiple autonomous signals"""
  
  def __init__(self):
    self.encoder = PatternEncoder()
    self.prediction_weight = 0.5
    self.curiosity_weight = 0.3
    self.consistency_weight = 0.2
  
  def compute_prediction_reward(self, prediction, actual):
    """Reward based on prediction accuracy"""
    try:
      # Encode both to vectors
      pred_vec = self.encoder.encode(prediction)
      actual_vec = self.encoder.encode(actual)
      
      # Compute similarity
      similarity = self.encoder.compute_similarity(pred_vec, actual_vec)
      
      # Similarity is already 0-1, use directly
      return max(0.0, min(1.0, similarity))
    except Exception as e:
      # Fallback: exact match
      return 1.0 if prediction == actual else 0.3
  
  def compute_curiosity_reward(self, new_info, existing_knowledge):
    """Reward for encountering novel information"""
    if not existing_knowledge:
      return 0.7  # Everything is novel at first
    
    try:
      new_vec = self.encoder.encode(new_info)
      
      # Find most similar existing knowledge
      max_similarity = 0.0
      for knowledge in existing_knowledge:
        know_vec = self.encoder.encode(knowledge)
        sim = self.encoder.compute_similarity(new_vec, know_vec)
        max_similarity = max(max_similarity, sim)
      
      # Novel but not completely alien = best
      novelty = 1.0 - max_similarity
      
      if 0.3 < novelty < 0.8:  # Sweet spot
        return 0.7 + novelty * 0.3
      else:
        return novelty * 0.5
    except:
      return 0.5  # Neutral
  
  def compute_consistency_reward(self, observation, existing_patterns):
    """Reward for confirming existing knowledge"""
    if not existing_patterns:
      return 0.5  # Neutral if no patterns yet
    
    try:
      obs_vec = self.encoder.encode(observation)
      
      # Check consistency with existing patterns
      consistencies = []
      for pattern in existing_patterns:
        pat_vec = self.encoder.encode(pattern)
        consistency = self.encoder.compute_similarity(obs_vec, pat_vec)
        consistencies.append(consistency)
      
      # High consistency = confirmation
      avg_consistency = np.mean(consistencies)
      return avg_consistency * 0.6  # Lower than novelty
    except:
      return 0.5
  
  def compute_reward(self, prediction=None, actual=None, new_info=None, 
                    existing_knowledge=None, observation=None, existing_patterns=None):
    """Unified autonomous reward computation"""
    rewards = []
    
    # 1. Prediction accuracy (if available)
    if prediction is not None and actual is not None:
      pred_reward = self.compute_prediction_reward(prediction, actual)
      rewards.append(pred_reward * self.prediction_weight)
    
    # 2. Curiosity (if new information)
    if new_info is not None:
      curiosity_reward = self.compute_curiosity_reward(new_info, existing_knowledge or [])
      rewards.append(curiosity_reward * self.curiosity_weight)
    
    # 3. Consistency (if observation available)
    if observation is not None and existing_patterns:
      consistency_reward = self.compute_consistency_reward(observation, existing_patterns)
      rewards.append(consistency_reward * self.consistency_weight)
    
    # Combine signals
    if rewards:
      return sum(rewards)
    else:
      return 0.5  # Neutral default

# -----------------------------
# Reward & Phase Classes
# -----------------------------
class RewardSystem:
  def compute_reward(self, success_rate, efficiency=1.0, safety=1.0):
    return success_rate * efficiency * safety

class MetaRewardSystem:
  def compute_meta_reward(self, success_rate, efficiency=1.0, novelty=1.0, safety=1.0):
    return success_rate * efficiency * novelty * safety

class PhaseController:
  def __init__(self):
    self.fast_done = False
    self.medium_done = False
    self.slow_done = False

  def check_phase(self):
    return self.fast_done and self.medium_done and self.slow_done

  def reset_phase(self):
    self.fast_done = False
    self.medium_done = False
    self.slow_done = False

# -----------------------------
# Sandbox / Self-Coding
# -----------------------------
class Sandbox:
  def execute(self, code_str, test_input):
    try:
      local_env = {}
      exec(code_str, {}, local_env)
      if "run" in local_env:
        return local_env["run"](test_input)
      return None
    except Exception as e:
      print(f"[Sandbox Error]: {e}")
      return None

# -----------------------------
# LLM / OpenAI Integration
# -----------------------------
class OpenAIAdvisor:
  def __init__(self, api_key=None):
    self.api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not self.api_key:
      print("[Warning] No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
      self.client = None
    else:
      self.client = OpenAI(api_key=self.api_key)
    self.conversation_history = []

  def chat(self, message, system_prompt=None):
    """Send a message to OpenAI and get a response."""
    if not self.client:
      return "[Error] OpenAI client not initialized. Please set your API key."
    
    try:
      messages = []
      if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
      
      # Add conversation history
      messages.extend(self.conversation_history)
      messages.append({"role": "user", "content": message})
      
      response = self.client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        temperature=0.7,
        max_tokens=1000
      )
      
      assistant_message = response.choices[0].message.content
      
      # Update conversation history
      self.conversation_history.append({"role": "user", "content": message})
      self.conversation_history.append({"role": "assistant", "content": assistant_message})
      
      # Keep only last 10 exchanges to manage context
      if len(self.conversation_history) > 20:
        self.conversation_history = self.conversation_history[-20:]
      
      return assistant_message
    except Exception as e:
      return f"[OpenAI Error]: {str(e)}"

  def suggest_routine(self, pattern_id, context_embedding, task_description=""):
    """Ask OpenAI to suggest code for a specific pattern."""
    if not self.client:
      # Fallback if no API key
      code_str = f"""
def run(data):
  # Fallback routine for {pattern_id}
  return sorted(data, reverse=True)
"""
      return code_str
    
    try:
      prompt = f"""Generate a Python function called 'run' that takes a parameter 'data' and performs {task_description if task_description else 'a useful transformation'}.
Pattern ID: {pattern_id}
Context embedding summary: {context_embedding[:3] if len(context_embedding) > 3 else context_embedding}

Return only the Python code, no explanations. The function should be simple and work with list inputs."""
      
      response = self.client.chat.completions.create(
        model="gpt-4",
        messages=[
          {"role": "system", "content": "You are a code generation assistant. Return only executable Python code without markdown formatting or explanations."},
          {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
      )
      
      code_str = response.choices[0].message.content
      # Clean up markdown code blocks if present
      if "```python" in code_str:
        code_str = code_str.split("```python")[1].split("```")[0].strip()
      elif "```" in code_str:
        code_str = code_str.split("```")[1].split("```")[0].strip()
      
      return code_str
    except Exception as e:
      print(f"[OpenAI Error in suggest_routine]: {e}")
      # Fallback code
      code_str = f"""
def run(data):
  # Fallback routine for {pattern_id}
  return sorted(data, reverse=True)
"""
      return code_str
  
  def clear_history(self):
    """Clear conversation history."""
    self.conversation_history = []

# -----------------------------
# Text & Web Learning
# -----------------------------

class TextLearner:
  """Learn from text through prediction"""
  
  def __init__(self, ai_system):
    self.ai = ai_system
    self.encoder = PatternEncoder()
  
  def learn_from_text(self, text, source="unknown"):
    """Learn by predicting and comparing"""
    sentences = self.split_sentences(text)
    
    if len(sentences) < 2:
      return
    
    total_reward = 0
    learned_patterns = 0
    
    # Learn by predicting next sentence
    for i in range(len(sentences) - 1):
      context = " ".join(sentences[max(0, i-2):i+1])  # Last few sentences
      actual_next = sentences[i + 1]
      
      # Try to predict based on learned patterns
      predicted_next = self.predict_next(context)
      
      # Compute reward from prediction accuracy
      reward = self.ai.autonomous_reward.compute_prediction_reward(
        predicted_next, actual_next
      )
      
      # Also compute curiosity reward
      existing_knowledge = [e["input"] for e in self.ai.fast_memory.entries[-100:]]
      curiosity_reward = self.ai.autonomous_reward.compute_curiosity_reward(
        actual_next, existing_knowledge
      )
      
      # Combined reward
      total_reward_this = (reward + curiosity_reward) / 2
      total_reward += total_reward_this
      
      # Store in fast memory
      context_embedding = self.encoder.encode(context)
      self.ai.fast_memory.add(
        context, predicted_next, actual_next, 
        total_reward_this, context_embedding,
        {"source": source, "type": "text_learning"}
      )
      
      learned_patterns += 1
    
   # Mark fast loop done
    self.ai.phase_controller.fast_done = True
    
    # Extract key concepts for medium memory
    self.extract_patterns(sentences, source)
    
    return {
      "sentences_processed": learned_patterns,
      "avg_reward": total_reward / max(1, learned_patterns),
      "source": source
    }
  
  def predict_next(self, context):
    """Predict next sentence based on learned patterns"""
    context_embedding = self.encoder.encode(context)
    
    # Find similar contexts in memory
    similar = self.ai.fast_memory.find_similar(context_embedding, n=3)
    
    if similar:
      # Use the actual from most similar context
      return similar[0][1]["actual"]
    else:
      # No similar context, return placeholder
      return "[no prediction available]"
  
  def extract_patterns(self, sentences, source):
    """Extract recurring patterns for medium memory"""
    # Simple pattern extraction: common words/phrases
    all_text = " ".join(sentences)
    words = re.findall(r'\\w+', all_text.lower())
    word_freq = Counter(words)
    
    # Store frequent patterns
    for word, freq in word_freq.most_common(10):
      if freq > 2:  # Appears multiple times
        pattern_id = f"{source}_{word}"
        pattern_code = f"# Pattern: '{word}' appears {freq} times in {source}"
        reward = min(1.0, freq / len(sentences))  # Frequency-based reward
        
        embedding = self.encoder.encode(word)
        self.ai.medium_memory.add_pattern(pattern_id, pattern_code, reward, embedding)
    
    self.ai.phase_controller.medium_done = True
  
  def split_sentences(self, text):
    """Simple sentence splitter"""
    # Split on periods, exclamation, question marks
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if s.strip()]

class WebLearner:
  """Learn from web content"""
  
  def __init__(self, ai_system):
    self.ai = ai_system
    self.text_learner = TextLearner(ai_system)
  
  def learn_from_url(self, url, timeout=10):
    """Fetch and learn from URL"""
    try:
      print(f"Fetching: {url}")
      response = requests.get(url, timeout=timeout, headers={
        'User-Agent': 'Mozilla/5.0 (Learning AI Bot)'
      })
      
      if response.status_code != 200:
        print(f"Failed to fetch: {response.status_code}")
        return None
      
      # Parse HTML
      soup = BeautifulSoup(response.content, 'html.parser')
      
      # Remove script and style elements
      for script in soup(["script", "style"]):
        script.decompose()
      
      # Get text
      text = soup.get_text()
      
      # Clean up whitespace
      lines = (line.strip() for line in text.splitlines())
      chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
      text = ' '.join(chunk for chunk in chunks if chunk)
      
      # Limit length for processing
      text = text[:5000]  # First 5000 chars
      
      # Learn from this text
      result = self.text_learner.learn_from_text(text, source=url)
      
      print(f"✓ Learned from {url}: {result['sentences_processed']} patterns")
      return result
      
    except Exception as e:
      print(f"Error learning from URL: {e}")
      return None
  
  def learn_from_file(self, filepath):
    """Learn from text file"""
    try:
      with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
      
      result = self.text_learner.learn_from_text(text, source=filepath)
      print(f"✓ Learned from {filepath}: {result['sentences_processed']} patterns")
      return result
      
    except Exception as e:
      print(f"Error learning from file: {e}")
      return None

# -----------------------------
# Visualization
# -----------------------------
class AIViz:
  def __init__(self, ai_system):
    self.ai = ai_system
    self.days = []
    self.fast_memory_counts = []
    self.medium_memory_counts = []
    self.long_term_counts = []
    self.daily_rewards = []

  def record_day(self, day):
    self.days.append(day)
    self.fast_memory_counts.append(len(self.ai.fast_memory.entries))
    self.medium_memory_counts.append(len(self.ai.medium_memory.patterns))
    self.long_term_counts.append(len(self.ai.long_term_memory.modules))
    if self.ai.fast_memory.entries:
      avg_reward = np.mean([e["reward"] for e in self.ai.fast_memory.entries[-10:]])
    else:
      avg_reward = 0
    self.daily_rewards.append(avg_reward)

  def plot_memory_growth(self):
    plt.figure(figsize=(10,5))
    plt.plot(self.days, self.fast_memory_counts, label="Fast Memory")
    plt.plot(self.days, self.medium_memory_counts, label="Medium Memory")
    plt.plot(self.days, self.long_term_counts, label="Long-Term Memory")
    plt.xlabel("Day")
    plt.ylabel("Entries/Modules")
    plt.title("AI Memory Growth Over Time")
    plt.legend()
    plt.show()

  def plot_rewards(self):
    plt.figure(figsize=(10,4))
    plt.plot(self.days, self.daily_rewards, color='green', marker='o')
    plt.xlabel("Day")
    plt.ylabel("Avg Fast Memory Reward")
    plt.title("Daily Reward Trend")
    plt.show()

  def plot_module_graph(self):
    G = nx.DiGraph()
    for module_id, data in self.ai.long_term_memory.modules.items():
      G.add_node(module_id, reward=np.mean(data["reward_history"]))
      for link in data["cross_domain_links"]:
        if link in self.ai.long_term_memory.modules:
          G.add_edge(module_id, link)
    plt.figure(figsize=(12,8))
    pos = nx.spring_layout(G, k=0.5)
    node_colors = [G.nodes[n]["reward"] for n in G.nodes]
    nx.draw(G, pos, with_labels=True, node_color=node_colors, cmap=plt.cm.viridis, node_size=800)
    sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis,
                 norm=plt.Normalize(vmin=min(node_colors, default=0), vmax=max(node_colors, default=1)))
    plt.colorbar(sm, label="Module Avg Reward", ax=plt.gca())
    plt.title("Long-Term Module Evolution & Cross-Domain Links")
    plt.show()

# -----------------------------
# Full Autonomous AI
# -----------------------------
class AutonomousAI:
  def __init__(self, api_key=None, memory_dir="./ai_memory", always_on=True, owner="user"):
    # Initialize ChromaDB for persistent storage
    print(f"[Init] Initializing memory system at: {memory_dir}")
    self.memory_dir = memory_dir
    self.chroma_client = chromadb.PersistentClient(
      path=memory_dir,
      settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
      )
    )

    # Core memories (persistent)
    self.fast_memory = FastMemory(self.chroma_client)
    self.medium_memory = MediumMemory(self.chroma_client)
    self.long_term_memory = LongTermMemory(self.chroma_client)

    print(f"[Init] Loaded {len(self.fast_memory.entries)} fast memory entries")
    print(f"[Init] Loaded {len(self.medium_memory.patterns)} patterns")
    print(f"[Init] Loaded {len(self.long_term_memory.modules)} modules")

    # Reward systems
    self.reward_system = RewardSystem()
    self.meta_reward_system = MetaRewardSystem()
    self.autonomous_reward = AutonomousRewardSystem()

    # Core components
    self.phase_controller = PhaseController()
    self.sandbox = Sandbox()
    self.encoder = PatternEncoder()

    # Learning systems
    self.llm_advisor = OpenAIAdvisor(api_key=api_key)
    self.text_learner = TextLearner(self)
    self.web_learner = WebLearner(self)

    # Autonomy core (minimal, human-aligned)
    self.log = CognitiveLog(memory_dir)
    self.resource_monitor = ResourceMonitor()
    self.self_core = SelfCore(owner=owner)
    self.task_memory = TaskMemory(self.chroma_client, self.log)
    self.scheduler = AutonomyScheduler()

    # Curiosity configuration
    self.curiosity_seed_urls = [
      "https://en.wikipedia.org/wiki/Special:Random"
    ]
    self.web_access_enabled = True

    # State
    self.running = True
    self.conversation_context = []
    self.last_user_interaction = time.time()
    self.autonomy_thread = None
    self.autonomy_running = False

    # Start always-on autonomy
    if always_on:
      self.start_autonomy()

    self.log.log_event("System initialized", "system", {
      "owner": owner,
      "always_on": always_on
    })
    print("[Init] Autonomous AI system ready!\n")

  def mark_user_active(self):
    self.last_user_interaction = time.time()

  def start_autonomy(self):
    if self.autonomy_running:
      return
    self.autonomy_running = True
    self.autonomy_thread = Thread(target=self._autonomy_loop, daemon=True)
    self.autonomy_thread.start()
    self.log.log_event("Autonomy started", "system")

  def stop_autonomy(self):
    self.autonomy_running = False
    if self.autonomy_thread:
      self.autonomy_thread.join(timeout=2)
    self.log.log_event("Autonomy stopped", "system")

  def _autonomy_loop(self):
    while self.running and self.autonomy_running:
      resource_state = self.resource_monitor.snapshot()
      user_active = (time.time() - self.last_user_interaction) < 5
      action = self.scheduler.choose_action(resource_state, user_active)
      if action:
        self._run_autonomy_action(action, resource_state)
      time.sleep(1.5 + (resource_state.get("strain", 0.0) * 2.0))

  def _run_autonomy_action(self, action, resource_state):
    self.log.log_raw(f"Autonomy action: {action}", "autonomy", {
      "strain": resource_state.get("strain", 0.0)
    })

    if action == "consolidation":
      self._autonomy_consolidate()
    elif action == "curiosity":
      self._autonomy_curiosity(resource_state)
    elif action == "prediction":
      self._autonomy_prediction()
    elif action == "alignment":
      self._autonomy_alignment()

  def _autonomy_consolidate(self):
    entries = self.fast_memory.entries[-25:]
    if not entries:
      return
    sample = random.choice(entries)
    pattern_id = f"auto_{hashlib.md5(str(sample['input']).encode()).hexdigest()[:8]}"
    helper_code = f"# Auto pattern from: {str(sample['input'])[:80]}"
    self.medium_loop(pattern_id, helper_code, float(sample.get("reward", 0.5)))
    self.log.log_event("Consolidated pattern", "autonomy", {"pattern_id": pattern_id})

  def _autonomy_curiosity(self, resource_state):
    if not self.web_access_enabled:
      return
    if resource_state.get("strain", 0.0) > 0.85:
      return
    url = random.choice(self.curiosity_seed_urls)
    self.log.log_event("Curiosity web fetch", "curiosity", {"url": url})
    self.learn_from_url(url)

  def _autonomy_prediction(self):
    entries = self.fast_memory.entries[-20:]
    if len(entries) < 2:
      return
    entry = random.choice(entries)
    reward = self.autonomous_reward.compute_reward(
      prediction=entry.get("prediction", ""),
      actual=entry.get("actual", ""),
      new_info=entry.get("actual", ""),
      existing_knowledge=[e.get("input", "") for e in entries]
    )
    self.log.log_event("Prediction drill", "prediction", {"reward": float(reward)})

  def _autonomy_alignment(self):
    task = self.task_memory.next_task()
    if not task:
      return
    task_data = [random.randint(0, 100) for _ in range(5)]
    result = self.process_task(task_data, task["description"])
    self.task_memory.complete_task(task["id"], result=result)

  # Fast / Medium / Slow Loops (now support universal patterns)
  def fast_loop(self, input_data, prediction, actual, explicit_reward=None, context=None):
    """Fast loop with autonomous reward computation"""
    
    # Compute reward autonomously if not provided
    if explicit_reward is not None:
      reward = explicit_reward
    else:
      # Use autonomous reward system
      existing_knowledge = [e["input"] for e in self.fast_memory.entries[-50:]]
      reward = self.autonomous_reward.compute_reward(
        prediction=prediction,
        actual=actual,
        new_info=actual,
        existing_knowledge=existing_knowledge
      )
    
    # Encode input for similarity search
    input_embedding = self.encoder.encode(input_data)
    
    # Store in fast memory
    self.fast_memory.add(input_data, prediction, actual, reward, input_embedding, context)
    self.phase_controller.fast_done = True
    
    return reward

  def medium_loop(self, pattern_id, helper_code, reward, embedding=None):
    """Medium loop with embedding support"""
    if embedding is None:
      embedding = self.encoder.encode(pattern_id)
    
    self.medium_memory.add_pattern(pattern_id, helper_code, reward, embedding)
    self.phase_controller.medium_done = True

  def slow_loop(self, module_id, code_ast, embedding, lesson_origin, version, reward, cross_links=None):
    """Slow loop unchanged"""
    self.long_term_memory.add_module(module_id, code_ast, embedding, lesson_origin, version, reward, cross_links)
    self.phase_controller.slow_done = True

  # Self-coding
  def self_code_module(self, pattern_id, test_input):
    code_str = f"""
def run(data):
  # Auto-generated routine for {pattern_id}
  return sorted(data)
"""
    result = self.sandbox.execute(code_str, test_input)
    if result:
      reward = self.reward_system.compute_reward(success_rate=1.0)
      module_id = hashlib.sha1(code_str.encode()).hexdigest()[:10]
      embedding = np.random.rand(10).tolist()
      self.slow_loop(module_id, code_str, embedding, pattern_id, "v1", reward)
      return module_id, reward
    return None, 0.0

  # Meta-loop / LLM advisory
  def meta_loop(self, pattern_id, context_embedding, task_description=""):
    proposed_code = self.llm_advisor.suggest_routine(pattern_id, context_embedding, task_description)
    test_input = [random.randint(0,50) for _ in range(5)]
    result = self.sandbox.execute(proposed_code, test_input)
    if result:
      meta_reward = self.meta_reward_system.compute_meta_reward(
        success_rate=1.0, efficiency=random.uniform(0.8,1.0), novelty=1.0
      )
      module_id = hashlib.sha1(proposed_code.encode()).hexdigest()[:10]
      embedding = np.random.rand(10).tolist()
      self.long_term_memory.add_module(module_id, proposed_code, embedding, pattern_id, "meta_v1", meta_reward)
      return module_id, meta_reward
    return None, 0.0

  # Run daily tasks
  def run_daily_tasks(self, human_inputs):
    for i, (input_data, test_input, pattern_id, task_desc) in enumerate(human_inputs):
      # Reset phase at start of each task
      self.phase_controller.reset_phase()
      
      prediction = sorted(input_data)
      actual = sorted(input_data)
      context = {"task_type": "simulation", "pattern_id": pattern_id}
      reward = self.fast_loop(input_data, prediction, actual, context=context)
      
      helper_code = f"# helper for {pattern_id}"
      self.medium_loop(pattern_id, helper_code, reward)
      
      module_id, code_reward = self.self_code_module(pattern_id, test_input)
      meta_module_id, meta_reward = self.meta_loop(pattern_id, np.random.rand(10).tolist(), task_desc)
      
      # Check if all phases completed
      if not self.phase_controller.check_phase():
        print(f"[Phase Warning] Task {i+1}: loops not aligned - Fast:{self.phase_controller.fast_done}, Medium:{self.phase_controller.medium_done}, Slow:{self.phase_controller.slow_done}")
      
      print(f"Task {i+1}: Pattern={pattern_id}, FastReward={reward:.2f}, "
         f"Module={module_id}, CodeReward={code_reward:.2f}, "
         f"MetaModule={meta_module_id}, MetaReward={meta_reward:.2f}")

  # Interactive Commands
  def chat(self, message):
    """Chat that learns through the three-loop system"""
    self.mark_user_active()
    self.log.log_event("User message", "chat", {"message": str(message)[:200]})
    
    # 1. Try to generate response from learned patterns
    response = self.generate_learned_response(message)
    confidence = self.estimate_confidence(response)
    
    # 2. If low confidence and advisor available, consult
    if confidence < 0.5 and self.llm_advisor.client:
      system_prompt = """You are an autonomous AI system with three-loop memory architecture:
      - Fast Memory: Immediate experiences and predictions
      - Medium Memory: Patterns and helper routines
      - Long-Term Memory: Evolved modules and cross-domain knowledge
      
      You can learn, adapt, and improve over time. You help users understand your processes and assist with tasks."""
      
      advisor_response = self.llm_advisor.chat(message, system_prompt)
      
      # Learn from advisor's response
      reward = self.autonomous_reward.compute_curiosity_reward(
        advisor_response,
        [e["input"] for e in self.fast_memory.entries[-20:]]
      )
      response = advisor_response
    elif confidence < 0.5:
      # No advisor, use best guess
      response = self.generate_fallback_response(message)
    
    # 3. Learn from this conversation (always!)
    self.learn_from_conversation(message, response)
    self.log.log_event("Assistant response", "chat", {"response": str(response)[:200]})
    
    return response
  
  def generate_learned_response(self, message):
    """Generate response using learned patterns"""
    # Encode message
    message_embedding = self.encoder.encode(message)
    
    # Find similar conversations
    similar = self.fast_memory.find_similar(message_embedding, n=5)
    
    if similar:
      # Use response from most similar high-reward interaction
      best = max(similar, key=lambda x: x[1].get("reward", 0))
      if best[1].get("reward", 0) > 0.6:
        # Adapt the response
        return best[1].get("actual", "[learning]")
    
    # Check medium memory for patterns
    good_patterns = self.medium_memory.find_best_patterns(threshold=0.6, limit=5)
    if good_patterns:
      # Use pattern as response template
      pattern_text = good_patterns[0][1]["helper_code"]
      return f"Based on learned patterns: {pattern_text}"
    
    return None
  
  def estimate_confidence(self, response):
    """Estimate confidence in generated response"""
    if response is None:
      return 0.0
    
    if "[learning]" in response or "Based on learned patterns" in response:
      return 0.3
    
    # Check if response is coherent
    if len(response) > 5 and len(response) < 500:
      return 0.7
    
    return 0.5
  
  def generate_fallback_response(self, message):
    """Generate simple fallback response"""
    message_lower = message.lower()
    
    # Simple pattern matching
    if any(word in message_lower for word in ["hello", "hi", "hey"]):
      return "Hello! I'm learning to converse. How can I help you?"
    elif "how are you" in message_lower:
      return "I'm processing and learning. Thank you for asking!"
    elif any(word in message_lower for word in ["what", "why", "how", "when", "where"]):
      return f"That's an interesting question about '{message}'. I'm still learning about this topic."
    elif "?" in message:
      return "I'm learning to answer questions. Could you teach me about this?"
    else:
      return "I'm learning from our conversation. Could you tell me more?"
  
  def learn_from_conversation(self, user_message, ai_response):
    """Learn from conversation through three loops"""
    
    # Fast loop: Store this exchange
    message_embedding = self.encoder.encode(user_message)
    
    # Predict: what we generated
    # Actual: same for now (will improve with user feedback)
    reward = self.autonomous_reward.compute_reward(
      prediction=ai_response,
      actual=ai_response,  # Assume correct for now
      new_info=user_message,
      existing_knowledge=[e["input"] for e in self.fast_memory.entries[-50:]]
    )
    
    self.fast_memory.add(
      user_message, ai_response, ai_response, reward,
      message_embedding,
      {"type": "conversation", "timestamp": time.time()}
    )
    self.phase_controller.fast_done = True
    
    # Medium loop: Extract conversation patterns
    pattern_id = f"chat_{hashlib.sha1(user_message.encode()).hexdigest()[:8]}"
    pattern_code = f"# User: {user_message[:50]}\\n# Response: {ai_response[:50]}"
    self.medium_loop(pattern_id, pattern_code, reward, message_embedding)
    
    # Slow loop: Build conversation module if pattern is strong
    if reward > 0.7 and len(self.fast_memory.entries) > 10:
      conv_module = f'''
def run(user_input):
    """Generated conversation handler"""
    # Pattern learned from: {pattern_id}
    return "{ai_response}"
'''
      module_id = hashlib.sha1(conv_module.encode()).hexdigest()[:10]
      module_embedding = self.encoder.encode(user_message).tolist()
      self.slow_loop(module_id, conv_module, module_embedding, pattern_id, "conv_v1", reward)
    
    # Update conversation context
    self.conversation_context.append({
      "user": user_message,
      "ai": ai_response,
      "reward": reward
    })
    if len(self.conversation_context) > 10:
      self.conversation_context = self.conversation_context[-10:]

  def process_task(self, task_data, task_description=""):
    """Process a single task interactively."""
    print(f"\n[Processing Task]: {task_description}")
    self.mark_user_active()
    self.log.log_event("Process task", "task", {"description": task_description})
    
    # Create a pattern ID
    pattern_id = f"interactive_{int(time.time())}"
    
    # Ensure task_data is a list
    if not isinstance(task_data, list):
      task_data = [task_data]
    
    test_input = task_data.copy()
    
    # Run through all three loops
    self.phase_controller.reset_phase()
    
    # Fast loop
    prediction = sorted(task_data)
    actual = sorted(task_data)
    context = {"task_type": "interactive", "description": task_description}
    fast_reward = self.fast_loop(task_data, prediction, actual, context=context)
    print(f"  ✓ Fast loop completed: reward={fast_reward:.2f}")
    
    # Medium loop
    helper_code = f"# Task: {task_description}\n# Pattern: {pattern_id}"
    self.medium_loop(pattern_id, helper_code, fast_reward)
    print(f"  ✓ Medium loop completed: pattern stored")
    
    # Slow loop via self-coding
    module_id, code_reward = self.self_code_module(pattern_id, test_input)
    print(f"  ✓ Slow loop completed: module={module_id}, reward={code_reward:.2f}")
    
    # Meta-loop with LLM
    meta_module_id, meta_reward = self.meta_loop(pattern_id, np.random.rand(10).tolist(), task_description)
    print(f"  ✓ Meta-loop completed: module={meta_module_id}, reward={meta_reward:.2f}")
    
    # Check phase completion
    if self.phase_controller.check_phase():
      print("  ✓ All phases synchronized successfully!")
    else:
      print(f"  ⚠ Phase sync issue - Fast:{self.phase_controller.fast_done}, Medium:{self.phase_controller.medium_done}, Slow:{self.phase_controller.slow_done}")

    self.log.log_event("Task processed", "task", {
      "pattern_id": pattern_id,
      "fast_reward": float(fast_reward),
      "code_reward": float(code_reward)
    })
    
    return {
      "pattern_id": pattern_id,
      "fast_reward": fast_reward,
      "module_id": module_id,
      "code_reward": code_reward,
      "meta_module_id": meta_module_id,
      "meta_reward": meta_reward
    }

  def show_status(self):
    """Display current system status."""
    print("\n" + "="*60)
    print("AUTONOMOUS AI SYSTEM STATUS")
    print("="*60)
    
    # Get ChromaDB collection counts
    fast_count = self.fast_memory.collection.count()
    medium_count = self.medium_memory.collection.count()
    long_term_count = self.long_term_memory.collection.count()
    
    print(f"Memory Storage: {self.memory_dir}")
    print(f"\nFast Memory:")
    print(f"  Cache: {len(self.fast_memory.entries)} entries")
    print(f"  Persistent: {fast_count} entries")
    print(f"\nMedium Memory:")
    print(f"  Active Patterns: {len(self.medium_memory.patterns)}")
    print(f"  Persistent: {medium_count} patterns")
    print(f"\nLong-Term Memory:")
    print(f"  Active Modules: {len(self.long_term_memory.modules)}")
    print(f"  Persistent: {long_term_count} modules")
    
    print(f"\nPhase Status:")
    print(f"  Fast Done: {self.phase_controller.fast_done}")
    print(f"  Medium Done: {self.phase_controller.medium_done}")
    print(f"  Slow Done: {self.phase_controller.slow_done}")
    print(f"  All Phases Aligned: {self.phase_controller.check_phase()}")
    
    if self.fast_memory.entries:
      avg_reward = np.mean([e["reward"] for e in self.fast_memory.entries[-10:]])
      print(f"\nRecent Average Reward: {avg_reward:.2f}")
    
    print("="*60 + "\n")

  def list_modules(self, limit=10):
    """List recent long-term memory modules."""
    print("\n" + "="*60)
    print("LONG-TERM MEMORY MODULES")
    print("="*60)
    
    modules = list(self.long_term_memory.modules.items())
    if not modules:
      print("No modules stored yet.")
      return
    
    for i, (module_id, data) in enumerate(modules[-limit:]):
      avg_reward = np.mean(data["reward_history"])
      print(f"\n{i+1}. Module ID: {module_id}")
      print(f"   Origin: {data['lesson_origin']}")
      print(f"   Versions: {len(data['versions'])}")
      print(f"   Avg Reward: {avg_reward:.2f}")
      print(f"   Usage: {len(data['reward_history'])} times")
    
    print("="*60 + "\n")
  
  def learn_from_text(self, text, source="user_input"):
    """Learn from text input"""
    self.mark_user_active()
    self.log.log_event("Learn from text", "learning", {"source": source, "chars": len(str(text))})
    result = self.text_learner.learn_from_text(text, source)
    return result
  
  def learn_from_url(self, url):
    """Learn from web URL"""
    self.mark_user_active()
    self.log.log_event("Learn from url", "learning", {"url": url})
    result = self.web_learner.learn_from_url(url)
    return result
  
  def learn_from_file(self, filepath):
    """Learn from file"""
    self.mark_user_active()
    self.log.log_event("Learn from file", "learning", {"path": filepath})
    result = self.web_learner.learn_from_file(filepath)
    return result

# -----------------------------
# Interactive Command Interface
# -----------------------------

def print_help():
  """Print available commands."""
  print("\n" + "="*60)
  print("AUTONOMOUS AI - AVAILABLE COMMANDS")
  print("="*60)
  print("AUTONOMY:")
  print("  start               - Start autonomous learning loop")
  print("  stop                - Stop autonomous learning loop")
  print("\nINTERACTION:")
  print("  chat <message>      - Chat and learn from conversation")
  print("  task <data>         - Process a task with data")
  print("\nLEARNING:")
  print("  learn <text>        - Learn from text input")
  print("  read <file>         - Learn from a text file")
  print("  browse <url>        - Learn from a webpage")
  print("\nSTATUS:")
  print("  status              - Show system status")
  print("  modules [n]         - List last n modules (default 10)")
  print("  patterns [n]        - List top n patterns (default 10)")
  print("\nOTHER:")
  print("  simulate [days]     - Run automated simulation")
  print("  visualize           - Show memory growth charts")
  print("  clear               - Clear conversation history")
  print("  help                - Show this help message")
  print("  exit/quit           - Exit the program")
  print("="*60 + "\n")

def run_interactive_mode(ai, viz):
  """Run the AI in interactive command mode."""
  print("\n" + "="*60)
  print("AUTONOMOUS AI SYSTEM - INTERACTIVE MODE")
  print("="*60)
  print("OpenAI API Status:", "Connected" if ai.llm_advisor.client else "Not Connected")
  print("\nType 'help' for available commands.")
  print("="*60 + "\n")
  
  day_counter = 0
  
  while ai.running:
    try:
      user_input = input("AI> ").strip()
      
      if not user_input:
        continue
      
      parts = user_input.split(maxsplit=1)
      command = parts[0].lower()
      args = parts[1] if len(parts) > 1 else ""
      
      if command in ["exit", "quit"]:
        print("Shutting down Autonomous AI system...")
        if ai.autonomous_mode:
          print("Stopping autonomous mode...")
          ai.stop_autonomous_mode()
        ai.running = False
        print("Goodbye!")
      
      elif command == "help":
        print_help()
      
      elif command == "start":
        if not ai.autonomy_running:
          ai.start_autonomy()
          print("✓ Autonomy loop started")
        else:
          print("⚠ Autonomy loop already running")
      
      elif command == "stop":
        if ai.autonomy_running:
          ai.stop_autonomy()
          print("✓ Autonomy loop stopped")
        else:
          print("⚠ Autonomy loop not running")
      
      elif command == "chat":
        if not args:
          print("Usage: chat <your message>")
        else:
          print("\nAI Response:")
          response = ai.chat(args)
          print(response)
          print()
      
      elif command == "task":
        if not args:
          print("Usage: task <data> [description]")
          print("Example: task [1,5,3,2,4] sort these numbers")
        else:
          try:
            # Try to parse the data
            if args.startswith('['):
              # Extract list and description
              list_end = args.find(']') + 1
              data_str = args[:list_end]
              description = args[list_end:].strip()
              
              task_data = json.loads(data_str)
            else:
              # Treat whole input as description
              task_data = [random.randint(0,100) for _ in range(5)]
              description = args
            
            result = ai.process_task(task_data, description)
            day_counter += 1
            viz.record_day(day_counter)
            
          except json.JSONDecodeError:
            print("Error: Invalid data format. Use JSON list format: [1,2,3,4,5]")
          except Exception as e:
            print(f"Error processing task: {e}")
      
      elif command == "status":
        ai.show_status()
      
      elif command == "modules":
        try:
          limit = int(args) if args else 10
          ai.list_modules(limit)
        except ValueError:
          print("Error: modules command takes a number argument")
      
      elif command == "simulate":
        try:
          days = int(args) if args else 7
          print(f"\n[Running {days}-day simulation...]")
          
          for day in range(1, days + 1):
            human_inputs = []
            tasks_today = random.randint(3, 7)
            
            for t in range(tasks_today):
              task_input = [random.randint(0,100) for _ in range(5)]
              test_input = [random.randint(0,50) for _ in range(5)]
              pattern_id = f"D{day}_T{t}"
              task_desc = f"Simulation task {t}"
              human_inputs.append((task_input, test_input, pattern_id, task_desc))
            
            ai.run_daily_tasks(human_inputs)
            day_counter += 1
            viz.record_day(day_counter)
            
            if day % 10 == 0:
              print(f"[Day {day}] {len(ai.fast_memory.entries)} fast memory entries")
          
          print(f"\n✓ Simulation complete! Processed {days} days.")
          ai.show_status()
          
        except ValueError:
          print("Error: simulate command takes a number argument")
      
      elif command == "visualize":
        if not viz.days:
          print("No data to visualize yet. Run some tasks or simulations first.")
        else:
          print("Generating visualizations...")
          try:
            viz.plot_memory_growth()
            viz.plot_rewards()
            viz.plot_module_graph()
            print("Visualizations complete!")
          except Exception as e:
            print(f"Visualization error: {e}")
      
      elif command == "clear":
        ai.llm_advisor.clear_history()
        ai.conversation_context = []
        print("✓ Conversation history cleared.")
      
      elif command == "learn":
        if not args:
          print("Usage: learn <text to learn from>")
        else:
          print(f"Learning from text...")
          result = ai.learn_from_text(args, source="user_input")
          if result:
            print(f"✓ Learned {result['sentences_processed']} patterns")
            print(f"  Average reward: {result['avg_reward']:.2f}")
            day_counter += 1
            viz.record_day(day_counter)
      
      elif command == "read":
        if not args:
          print("Usage: read <filepath>")
        else:
          result = ai.learn_from_file(args)
          if result:
            day_counter += 1
            viz.record_day(day_counter)
      
      elif command == "browse":
        if not args:
          print("Usage: browse <url>")
        else:
          result = ai.learn_from_url(args)
          if result:
            day_counter += 1
            viz.record_day(day_counter)
      
      elif command == "patterns":
        try:
          limit = int(args) if args else 10
          print("\n" + "="*60)
          print("TOP MEDIUM MEMORY PATTERNS")
          print("="*60)
          patterns = ai.medium_memory.find_best_patterns(threshold=0.0, limit=limit)
          if not patterns:
            print("No patterns stored yet.")
          else:
            for i, (pid, pdata) in enumerate(patterns, 1):
              print(f"\n{i}. Pattern: {pid}")
              print(f"   Avg Reward: {pdata['avg_reward']:.2f}")
              print(f"   Usage: {pdata['usage_count']} times")
              print(f"   Code: {pdata['helper_code'][:100]}...")
          print("="*60 + "\n")
        except ValueError:
          print("Error: patterns command takes a number argument")
      
      else:
        print(f"Unknown command: '{command}'. Type 'help' for available commands.")
    
    except KeyboardInterrupt:
      print("\n\nInterrupted. Type 'exit' to quit.")
    except Exception as e:
      print(f"Error: {e}")

# -----------------------------
# Main Entry Point
# -----------------------------

if __name__ == "__main__":
  print("Initializing Autonomous AI System...")
  
  # Check for API key
  api_key = os.getenv("OPENAI_API_KEY")
  if not api_key:
    print("\n⚠ WARNING: OPENAI_API_KEY not found in environment variables.")
    print("Set it with: export OPENAI_API_KEY='your-key-here'")
    print("The system will still work but with limited AI capabilities.\n")
  
  # Check for command line arguments
  mode = "interactive"  # default mode
  if len(sys.argv) > 1:
    if sys.argv[1] == "--simulate":
      mode = "simulate"
      days = int(sys.argv[2]) if len(sys.argv) > 2 else 365
  
  ai = AutonomousAI(api_key=api_key)
  viz = AIViz(ai)
  
  if mode == "simulate":
    # Automated multi-day simulation mode
    print(f"Running automated simulation for {days} days...")
    years = days // 365
    remaining_days = days % 365

    day_counter = 0
    for year in range(1, years + 1):
      for day in range(1, 366):
        human_inputs = []
        tasks_today = random.randint(5, 10)
        for t in range(tasks_today):
          task_input = [random.randint(0,100) for _ in range(5)]
          test_input = [random.randint(0,50) for _ in range(5)]
          pattern_id = f"Y{year}D{day}_T{t}"
          task_desc = f"Automated task"
          human_inputs.append((task_input, test_input, pattern_id, task_desc))
        ai.run_daily_tasks(human_inputs)
        day_counter += 1
        viz.record_day(day_counter)
        if day_counter % 100 == 0:
          print(f"[Progress] Day {day_counter}/{days}")
    
    # Process remaining days
    for day in range(1, remaining_days + 1):
      human_inputs = []
      tasks_today = random.randint(5, 10)
      for t in range(tasks_today):
        task_input = [random.randint(0,100) for _ in range(5)]
        test_input = [random.randint(0,50) for _ in range(5)]
        pattern_id = f"D{day_counter + day}_T{t}"
        task_desc = f"Automated task"
        human_inputs.append((task_input, test_input, pattern_id, task_desc))
      ai.run_daily_tasks(human_inputs)
      day_counter += 1
      viz.record_day(day_counter)

    # Show visualizations
    viz.plot_memory_growth()
    viz.plot_rewards()
    viz.plot_module_graph()
  else:
    # Interactive mode
    run_interactive_mode(ai, viz)