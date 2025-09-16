from github_actions_checker import GitHubActionsChecker
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def test_session_debug():
    checker = GitHubActionsChecker()
    
    print("Testing session debugging...")
    
    # Just test the debug info at startup
    await checker.run_check()

# Run test
if __name__ == "__main__":
    asyncio.run(test_session_debug())
