#!/usr/bin/env python3
"""Test script to verify ChromaDB persistence works correctly."""

import sys
import os

# Test 1: Initialize the system and add some data
print("=" * 60)
print("TEST 1: Initialize system and add learning data")
print("=" * 60)

from AutonomousAI import AutonomousAI

# Create AI instance
ai = AutonomousAI(memory_dir="./test_memory")
print("\n✓ System initialized successfully\n")

# Show initial status
ai.show_status()

# Add some learning data
print("\n" + "=" * 60)
print("Adding learning data...")
print("=" * 60)

# Learn from some text
text = """
Artificial intelligence enables machines to learn from experience.
Machine learning algorithms identify patterns in data.
Deep learning uses neural networks with many layers.
"""

print(f"\nLearning from text: '{text.strip()[:50]}...'")
ai.learn_from_text(text)
print("✓ Text learning completed\n")

# Show status after learning
ai.show_status()

# Test 2: Restart the system and verify data persists
print("\n" + "=" * 60)
print("TEST 2: Restart system and verify persistence")
print("=" * 60)

# Delete the AI instance to simulate restart
del ai
print("\n✓ System shutdown (instance deleted)\n")

# Reinitialize
print("Reinitializing system from persistent storage...")
ai = AutonomousAI(memory_dir="./test_memory")
print("✓ System reinitialized\n")

# Show status after restart
ai.show_status()

# Verify data persists
if len(ai.fast_memory.entries) > 0:
    print("✓ SUCCESS: Fast memory persisted across restart!")
else:
    print("✗ FAILURE: Fast memory lost after restart")

if len(ai.medium_memory.patterns) > 0:
    print("✓ SUCCESS: Medium memory persisted across restart!")
else:
    print("✗ FAILURE: Medium memory lost after restart")

# Test similarity search
print("\n" + "=" * 60)
print("TEST 3: Verify similarity search works")
print("=" * 60)

test_input = "neural networks"
similar = ai.fast_memory.find_similar(test_input, limit=3)
print(f"\nSearching for patterns similar to: '{test_input}'")
print(f"Found {len(similar)} similar entries:")
for i, (entry, similarity) in enumerate(similar, 1):
    pattern_preview = str(entry.get("pattern", ""))[:50]
    print(f"  {i}. Similarity: {similarity:.3f} - Pattern: {pattern_preview}...")

if len(similar) > 0:
    print("\n✓ SUCCESS: Similarity search working!")
else:
    print("\n✗ FAILURE: Similarity search returned no results")

print("\n" + "=" * 60)
print("PERSISTENCE TESTS COMPLETED")
print("=" * 60)
print("\nMemory directory: ./test_memory")
print("You can delete this directory to clean up test data.")
