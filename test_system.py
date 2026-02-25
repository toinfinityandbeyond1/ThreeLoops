#!/usr/bin/env python3
"""
Test script for AutonomousAI system
"""

import sys
import os

# Test imports
try:
    print("Testing imports...")
    import numpy as np
    print("✓ numpy imported")
    
    from openai import OpenAI
    print("✓ openai imported")
    
    import matplotlib.pyplot as plt
    print("✓ matplotlib imported")
    
    import networkx as nx
    print("✓ networkx imported")
    
    print("\n✓ All imports successful!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test AutonomousAI class
try:
    print("\nTesting AutonomousAI system...")
    from AutonomousAI import AutonomousAI, AIViz
    
    # Create AI instance (without API key for basic testing)
    ai = AutonomousAI(api_key=None)
    print("✓ AutonomousAI instance created")
    
    # Test phase controller
    ai.phase_controller.reset_phase()
    print(f"✓ Phase controller initialized - Fast:{ai.phase_controller.fast_done}, Medium:{ai.phase_controller.medium_done}, Slow:{ai.phase_controller.slow_done}")
    
    # Test fast memory
    ai.fast_memory.add([1,2,3], [1,2,3], [1,2,3], 0.5)
    print(f"✓ Fast memory working - {len(ai.fast_memory.entries)} entries")
    
    # Test medium memory
    ai.medium_memory.add_pattern("test_pattern", "# test code", 0.7)
    print(f"✓ Medium memory working - {len(ai.medium_memory.patterns)} patterns")
    
    # Test long-term memory
    ai.long_term_memory.add_module("test_module", "# code", [0.1, 0.2], "test", "v1", 0.8)
    print(f"✓ Long-term memory working - {len(ai.long_term_memory.modules)} modules")
    
    # Test sandbox
    test_code = """
def run(data):
    return sorted(data)
"""
    result = ai.sandbox.execute(test_code, [3, 1, 2])
    print(f"✓ Sandbox working - result: {result}")
    
    # Test phase synchronization
    ai.phase_controller.fast_done = True
    ai.phase_controller.medium_done = True
    ai.phase_controller.slow_done = True
    sync_status = ai.phase_controller.check_phase()
    print(f"✓ Phase synchronization - All phases aligned: {sync_status}")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    print("\nYou can now run the AI system using:")
    print("  python3 AutonomousAI.py")
    print("\nOr set your OpenAI API key and try:")
    print("  export OPENAI_API_KEY='your-key-here'")
    print("  python3 AutonomousAI.py")
    
except Exception as e:
    print(f"\n✗ Error testing AutonomousAI: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
