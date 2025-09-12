#!/usr/bin/env python3
"""
Next Friday & Monday Badminton Slot Checker
Automatically checks the next upcoming Friday and Monday availability (2 dates only)
"""

import asyncio
import os
import sys
import logging
from datetime import datetime

# Configure logging to reduce emoji errors
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/friday_monday_checker.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import the main checker
from complete_e2e_test import CompleteE2EChecker

def main():
    """Entry point for Friday & Monday checker"""
    print("=" * 70)
    print("🏸 NEXT FRIDAY & MONDAY BADMINTON SLOT CHECKER")
    print("=" * 70)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔍 Checking ONLY the next upcoming Friday and Monday")
    print("📡 Will send Telegram notifications if slots are found")
    print("=" * 70)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Run the checker
    checker = CompleteE2EChecker()
    asyncio.run(checker.run_complete_e2e_test())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n❌ Checker stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
