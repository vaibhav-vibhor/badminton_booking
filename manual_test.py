import asyncio
import logging
from main import BadmintonSlotChecker

async def manual_login_test():
    """Test script that allows manual login intervention"""
    
    # Set up logging to see what's happening
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("🏸 Manual Login Test Mode")
    print("=" * 40)
    print("This will open the browser and let you login manually,")
    print("then continue with automated slot checking.")
    print()
    
    try:
        # Create checker instance
        checker = BadmintonSlotChecker()
        
        # Run a single check with manual intervention
        print("🚀 Starting manual login test...")
        
        # This will use our existing logic but with visible browser
        result = await checker._check_slots_with_manual_login()
        
        if result:
            print("✅ Manual login test successful!")
            print("📱 Check your Telegram for slot notifications")
        else:
            print("❌ Test failed - check the logs above")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    asyncio.run(manual_login_test())
