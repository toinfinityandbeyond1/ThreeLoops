#!/usr/bin/env python3
"""
Example usage of AutonomousAI system without OpenAI API
This demonstrates how to use the system interactively
"""

from AutonomousAI import AutonomousAI, AIViz
import time

def main():
    print("="*60)
    print("AUTONOMOUS AI - EXAMPLE USAGE")
    print("="*60)
    
    # Create AI instance
    print("\nInitializing AI system...")
    ai = AutonomousAI(api_key=None)  # No API key for this example
    viz = AIViz(ai)
    
    print("✓ AI system initialized")
    
    # Example 1: Process a simple task
    print("\n" + "="*60)
    print("Example 1: Processing a simple task")
    print("="*60)
    
    task_data = [5, 3, 8, 1, 9]
    result = ai.process_task(task_data, "Sort these numbers")
    
    # Example 2: Show system status
    print("\n" + "="*60)
    print("Example 2: System Status")
    print("="*60)
    ai.show_status()
    
    # Example 3: Process multiple tasks
    print("\n" + "="*60)
    print("Example 3: Processing multiple tasks")
    print("="*60)
    
    tasks = [
        ([10, 20, 5], "Process numbers"),
        ([1, 2, 3, 4], "Sequence analysis"),
        ([100, 50, 25], "Data transformation")
    ]
    
    for i, (data, desc) in enumerate(tasks, 1):
        print(f"\n--- Task {i} ---")
        ai.process_task(data, desc)
        viz.record_day(i)
    
    # Example 4: List learned modules
    print("\n" + "="*60)
    print("Example 4: Learned Modules")
    print("="*60)
    ai.list_modules(limit=5)
    
    # Example 5: Run a small simulation
    print("\n" + "="*60)
    print("Example 5: Running 3-day simulation")
    print("="*60)
    
    import random
    for day in range(1, 4):
        print(f"\n--- Day {day} ---")
        human_inputs = []
        for t in range(3):
            task_input = [random.randint(0,100) for _ in range(5)]
            test_input = [random.randint(0,50) for _ in range(5)]
            pattern_id = f"D{day}_T{t}"
            task_desc = f"Simulation task {t}"
            human_inputs.append((task_input, test_input, pattern_id, task_desc))
        
        ai.run_daily_tasks(human_inputs)
        viz.record_day(len(viz.days) + 1)
    
    # Final status
    print("\n" + "="*60)
    print("FINAL SYSTEM STATUS")
    print("="*60)
    ai.show_status()
    
    print("\n" + "="*60)
    print("Example complete!")
    print("="*60)
    print("\nTo use the interactive mode, run:")
    print("  python3 AutonomousAI.py")
    print("\nTo enable OpenAI features, set your API key:")
    print("  export OPENAI_API_KEY='your-key-here'")
    print("="*60)

if __name__ == "__main__":
    main()
