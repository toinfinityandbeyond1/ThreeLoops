#!/usr/bin/env python3
"""
Demonstration of the Autonomous Learning System
Shows the system learning without OpenAI API
"""

from AutonomousAI import AutonomousAI, AIViz

def main():
    print("="*70)
    print("AUTONOMOUS AI - SELF-SUPERVISED LEARNING DEMO")
    print("="*70)
    print("\nThis demo shows the AI learning autonomously through:")
    print("- Prediction-based rewards")
    print("- Pattern recognition from text")
    print("- Conversation learning")
    print("- All WITHOUT requiring OpenAI API!")
    print("="*70)
    
    # Initialize AI (no API key needed!)
    ai = AutonomousAI(api_key=None)
    viz = AIViz(ai)
    
    # Demo 1: Learn from text
    print("\n\n" + "="*70)
    print("DEMO 1: LEARNING FROM TEXT")
    print("="*70)
    
    sample_text = """
    The quick brown fox jumps over the lazy dog.
    Machine learning is a subset of artificial intelligence.
    Neural networks are inspired by biological neurons.
    Deep learning uses multiple layers of neural networks.
    The AI learns patterns from data through experience.
    """
    
    print("\nTeaching the AI some text...")
    print(f"Text: {sample_text[:100]}...")
    result = ai.learn_from_text(sample_text, source="demo_text")
    print(f"\n✓ Learned {result['sentences_processed']} sentence patterns")
    print(f"  Average prediction reward: {result['avg_reward']:.2f}")
    
    # Demo 2: Conversation learning
    print("\n\n" + "="*70)
    print("DEMO 2: CONVERSATION LEARNING")
    print("="*70)
    
    conversations = [
        "Hello",
        "How are you?",
        "What is machine learning?",
        "Thank you",
        "Goodbye"
    ]
    
    print("\nHaving a conversation with the AI...")
    for msg in conversations:
        print(f"\nYou: {msg}")
        response = ai.chat(msg)
        print(f"AI: {response}")
    
    # Demo 3: Check what it learned
    print("\n\n" + "="*70)
    print("DEMO 3: WHAT THE AI LEARNED")
    print("="*70)
    
    print(f"\nFast Memory: {len(ai.fast_memory.entries)} experiences")
    print(f"Medium Memory: {len(ai.medium_memory.patterns)} patterns")
    print(f"Long-Term Memory: {len(ai.long_term_memory.modules)} modules")
    
    # Show some patterns
    print("\nTop learned patterns:")
    patterns = ai.medium_memory.find_best_patterns(threshold=0.0, limit=5)
    for i, (pid, pdata) in enumerate(patterns, 1):
        print(f"{i}. {pid}: reward={pdata['avg_reward']:.2f}, used {pdata['usage_count']} times")
    
    # Demo 4: Test pattern retrieval
    print("\n\n" + "="*70)
    print("DEMO 4: PATTERN-BASED RESPONSE")
    print("="*70)
    
    print("\nAsking a similar question...")
    test_msg = "Hello there"
    print(f"You: {test_msg}")
    
    # Find similar past conversations
    test_embedding = ai.encoder.encode(test_msg)
    similar = ai.fast_memory.find_similar(test_embedding, n=3)
    
    if similar:
        print(f"\nFound {len(similar)} similar past experiences:")
        for i, (sim_score, entry) in enumerate(similar, 1):
            print(f"  {i}. Similarity: {sim_score:.2f}")
            print(f"     Past input: {entry['input']}")
            print(f"     Response: {entry['actual']}")
    
    response = ai.chat(test_msg)
    print(f"\nAI: {response}")
    
    # Demo 5: Show autonomous reward computation
    print("\n\n" + "="*70)
    print("DEMO 5: AUTONOMOUS REWARD SIGNALS")
    print("="*70)
    
    print("\nThe AI generates its own reward signals:")
    print("- Prediction accuracy: How well it predicted the next pattern")
    print("- Curiosity: How novel the information is")
    print("- Consistency: How well it confirms existing knowledge")
    
    # Recent rewards
    if ai.fast_memory.entries:
        recent_rewards = [e["reward"] for e in ai.fast_memory.entries[-10:]]
        print(f"\nLast 10 rewards: {[f'{r:.2f}' for r in recent_rewards]}")
        print(f"Average: {sum(recent_rewards)/len(recent_rewards):.2f}")
        print(f"Trend: {'Improving' if recent_rewards[-1] > recent_rewards[0] else 'Declining'}")
    
    # Demo 6: Phase coordination
    print("\n\n" + "="*70)
    print("DEMO 6: THREE-LOOP COORDINATION")
    print("="*70)
    
    print("\nProcessing a task through all three loops...")
    ai.process_task([5, 2, 8, 1, 9], "Sort these numbers")
    
    # Final summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    ai.show_status()
    
    print("\n" + "="*70)
    print("KEY INSIGHTS")
    print("="*70)
    print("✓ The AI learns autonomously through prediction")
    print("✓ No hardcoded language rules - patterns emerge naturally")
    print("✓ OpenAI is optional - just helps accelerate learning")
    print("✓ The three-loop system handles ANY data type")
    print("✓ Reward signals are self-generated from prediction accuracy")
    print("✓ Phase coordination ensures consistent learning")
    print("="*70)
    
    print("\n\nTo interact with the AI, run: python3 AutonomousAI.py")
    print("Try these commands:")
    print("  chat <message>  - Have a conversation")
    print("  learn <text>    - Teach it something")
    print("  browse <url>    - Let it learn from the web")

if __name__ == "__main__":
    main()
