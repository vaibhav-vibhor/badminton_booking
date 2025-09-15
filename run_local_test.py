#!/usr/bin/env python3
"""
Local testing script with environment variable support
"""

import os
import sys
from pathlib import Path
import asyncio
import logging

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_env_file():
    """Load environment variables from .env file if it exists"""
    env_file = Path(__file__).parent / '.env'
    
    if not env_file.exists():
        logger.warning("⚠️ No .env file found. Create one from .env.example for local testing.")
        logger.info("💡 Copy .env.example to .env and fill in your credentials:")
        logger.info("   cp .env.example .env")
        return False
    
    logger.info("📁 Loading environment variables from .env file...")
    
    try:
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=VALUE format
                if '=' not in line:
                    logger.warning(f"⚠️ Invalid format on line {line_num}: {line}")
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Set environment variable
                os.environ[key] = value
                logger.debug(f"✅ Set {key}={value[:10]}...")
        
        logger.info("✅ Environment variables loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to load .env file: {e}")
        return False

def verify_credentials():
    """Verify that required credentials are available"""
    required_vars = ['PHONE_NUMBER', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value in ['your_phone_number_here', 'your_bot_token_from_botfather', 'your_chat_id']:
            missing_vars.append(var)
    
    if missing_vars:
        logger.error("❌ Missing or invalid credentials:")
        for var in missing_vars:
            logger.error(f"   • {var}")
        logger.error("")
        logger.error("📝 Please update your .env file with real credentials:")
        logger.error("   1. Copy .env.example to .env")
        logger.error("   2. Replace placeholder values with your real credentials")
        logger.error("   3. Run this script again")
        return False
    
    logger.info("✅ All required credentials are configured")
    return True

async def run_local_test():
    """Run the main checker script locally"""
    try:
        # Import the main checker
        from github_actions_checker import GitHubActionsChecker
        
        logger.info("🏸 Starting local badminton slot checker...")
        
        # Create checker instance
        checker = GitHubActionsChecker()
        
        # Run the check
        await checker.run_check()
        
        logger.info("✅ Local test completed")
        
    except Exception as e:
        logger.error(f"❌ Local test failed: {e}")
        raise

def main():
    """Main function for local testing"""
    print("🏸 Badminton Checker - Local Test")
    print("=" * 50)
    
    # Load environment variables from .env file
    if not load_env_file():
        return 1
    
    # Verify credentials
    if not verify_credentials():
        return 1
    
    # Show configuration (masked)
    phone = os.getenv('PHONE_NUMBER', '')
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    
    logger.info("📋 Configuration:")
    logger.info(f"   📱 Phone: {phone[:3]}***{phone[-3:] if len(phone) > 6 else '***'}")
    logger.info(f"   🤖 Bot Token: {bot_token[:10]}***{bot_token[-10:] if len(bot_token) > 20 else '***'}")
    logger.info(f"   💬 Chat ID: {chat_id[:3]}***{chat_id[-3:] if len(chat_id) > 6 else '***'}")
    
    # Optional settings
    headless = os.getenv('HEADLESS_MODE', 'false').lower() == 'true'
    debug = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
    
    if headless:
        logger.info("   🚫 Headless mode: ENABLED (no browser window)")
    else:
        logger.info("   👁️ Headless mode: DISABLED (browser window will show)")
    
    if debug:
        logger.info("   🐛 Debug mode: ENABLED (extra logging)")
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("")
    logger.info("🚀 Starting test run...")
    
    try:
        # Run the async test
        asyncio.run(run_local_test())
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️ Test cancelled by user")
        return 0
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
