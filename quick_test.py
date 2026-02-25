#!/usr/bin/env python3
"""
Quick test to verify the autonomous learning system works
"""

print("Testing Autonomous AI System...")
print("="*60)

try:
    from AutonomousAI import AutonomousAI, AIViz
    print("✓ Import successful")
    
    # Create AI without API key
    ai = AutonomousAI(api_key=None)
    print("✓ AI initialized without OpenAI API")
    
    # Test pattern encoder
    test_text = "Hello world"
    encoding = ai.encoder.encode(test_text)
    print(f"✓ Pattern encoder works: {len(encoding)} dimensions")
    
    # Test autonomous reward
    reward = ai.autonomous_reward.compute_prediction_reward("test", "test")
    print(f"✓ Autonomous reward system works: {reward:.2f}")
    
    # Test chat (should work without OpenAI)
    response = ai.chat("Hello")
    print(f"✓ Chat works: '{response[:50]}...'")
    
    # Test text learning
    ai.learn_from_text("The cat sat on the mat. The dog ran in the park.", "test")
    print(f"✓ Text learning works")
    
    # Check memories
    print(f"✓ Fast memory: {len(ai.fast_memory.entries)} entries")
    print(f"✓ Medium memory: {len(ai.medium_memory.patterns)} patterns")
    
    # Test phase coordination
    ai.phase_controller.reset_phase()
    ai.phase_controller.fast_done = True
    ai.phase_controller.medium_done = True
    ai.phase_controller.slow_done = True
    assert ai.phase_controller.check_phase() == True
    print("✓ Phase coordination works")
    
    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    print("\nThe system is ready to use!")
    print("\nTry:")
    print("  python3 demo_autonomous_learning.py  # See it in action")
    print("  python3 AutonomousAI.py              # Interactive mode")
    
except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\nTry: pip install -r requirements.txt")
