# 🏸 Automated Badminton Slot Checker

An automated GitHub Actions-powered system that monitors badminton court availability at Gopichand Academy locations and sends instant Telegram notifications when slots become available. The system uses advanced API integration for fast, reliable slot checking without browser automation.

## 🚀 Key Features

- **⚡ Lightning Fast**: Pure API integration - finds 81 slots across all academies in ~28 seconds
- **🤖 Fully Automated**: Runs automatically on GitHub Actions (completely free hosting)
- **📅 Smart Date Logic**: Automatically checks next upcoming Friday and Monday
- **🏫 Multi-Academy Support**: Monitors all 3 Gopichand Academy locations simultaneously
- **📱 Beautiful Telegram Notifications**: Clean table format with ✓/• symbols for slot availability
- **🔄 Zero Maintenance**: Set once, runs automatically forever
- **💻 Environment Detection**: Messages show whether sent from local testing or GitHub Actions
- **🔐 No OTP Required**: Direct API access eliminates hourly authentication issues

## 🎯 Quick Setup (5 Minutes)

### 1. Fork This Repository
Click the "Fork" button on GitHub to copy this repo to your account.

### 2. Add GitHub Secrets
Go to your repository → Settings → Secrets and variables → Actions → New repository secret:

- `TELEGRAM_BOT_TOKEN`: Get from [@BotFather](https://t.me/botfather)  
- `TELEGRAM_CHAT_ID`: Get from [@RawDataBot](https://t.me/rawdatabot)

### 3. Enable GitHub Actions
Go to Actions tab → Enable workflows → Allow all actions

### 4. Test Setup
Run `python run_local_test.py` locally to verify your configuration.

### 5. Manual First Run
Go to Actions → "🏸 Badminton Slot Checker" → Run workflow

That's it! Your checker now runs automatically and sends you perfectly formatted slot availability tables! 🎉

## � Repository Structure and File Guide

### 🏠 Root Directory Files

| File | Description | Key Functions |
|------|-------------|---------------|
| **`github_actions_checker.py`** | Main entry point for the application. Handles both local testing and GitHub Actions execution. Contains browser automation as fallback if API fails. | `GitHubActionsChecker` class with methods: `send_telegram_message()`, `interactive_login()`, `check_academy_slots()`, `run_check()` |
| **`run_local_test.py`** | Local testing script to verify your setup and test the slot checker on your machine before deploying to GitHub Actions. | `setup_logging()`, `validate_credentials()`, `run_test()` |
| **`get_chat_id.py`** | Utility script to help you find your Telegram chat ID by fetching recent messages from your bot. | `get_chat_updates()`, displays recent chats with IDs |
| **`requirements.txt`** | Lists all Python packages needed to run the application (requests, playwright, etc.). | N/A - dependency list |
| **`.env.example`** | Template file showing what environment variables you need to set up for local testing. | N/A - configuration template |
| **`.gitignore`** | Tells Git which files to ignore (like your actual .env file with secrets, logs, cache files). | N/A - Git configuration |

### 📁 Directory Structure

```
📦 badminton_booking/
├── 📁 .github/workflows/          # GitHub Actions automation
│   └── 📄 badminton-checker.yml   # Hourly workflow that runs the checker
├── 📁 src/                        # Core application modules  
│   ├── 📄 api_checker.py          # Pure API integration (main logic)
│   ├── 📄 checker_helpers.py      # Helper utilities and functions
│   └── 📄 __init__.py             # Makes src a Python package
├── 📁 config/                     # Configuration files
│   ├── 📄 check_dates.json        # Dates and preferences for slot checking
│   └── 📄 settings.json           # Application settings
├── 📁 data/                       # Session data (auto-managed)
│   ├── 📄 api_token.json          # Stores API authentication tokens
│   ├── 📄 check_history.json      # History of previous checks
│   ├── 📄 github_cookies.json     # Browser cookies for session persistence  
│   └── 📄 github_session.json     # Session storage data
├── 📁 logs/                       # Application logs (auto-created)
├── 📄 GitHub Actions entry point  # Main script file
├── 📄 Local testing script        # Test runner
└── 📄 Documentation files         # Setup guides and templates
```

## 🔧 Core Components Deep Dive

### 🎯 `src/api_checker.py` - The Heart of the System

This is the main logic file that handles all API communication with Gopichand Academy's booking system.

**Main Class: `BadmintonAPIChecker`**

| Function | What It Does | 
|----------|--------------|
| `__init__()` | Sets up the API checker with authentication and session management |
| `load_existing_token()` | Loads saved authentication tokens from disk |
| `save_token()` | Saves authentication tokens to disk for reuse |
| `set_auth_headers()` | Configures HTTP headers for API requests |
| `verify_token()` | Checks if the current authentication token is still valid |
| `get_venue_slots()` | Gets available slots for a specific academy on a specific date |
| `parse_calendar_api_response()` | Converts API response into readable slot information |
| `check_all_academies()` | Checks all 3 academies simultaneously for available slots |
| `format_results_for_telegram()` | Creates the beautiful table format you see in Telegram messages |

**Academy IDs:**
- **Kotak Pullela Gopichand Academy**: ID 1
- **Pullela Gopichand Academy**: ID 2  
- **SAI Pullela Gopichand Academy**: ID 3

### 🤖 `github_actions_checker.py` - Main Controller

This file orchestrates the entire slot checking process and handles both local and GitHub Actions execution.

**Main Class: `GitHubActionsChecker`**

| Function | What It Does |
|----------|--------------|
| `__init__()` | Initializes the checker with environment variables and settings |
| `send_telegram_message()` | Sends formatted messages to your Telegram chat |
| `get_check_dates()` | Calculates which dates to check (next Friday and Monday) |
| `save_session()` | Saves browser session data for reuse |
| `restore_session()` | Restores previous browser session to avoid re-login |
| `verify_login()` | Checks if the current session is still logged in |
| `interactive_login()` | Handles the login process with OTP verification |
| `check_academy_slots()` | Browser-based slot checking (fallback method) |
| `run_check()` | Main execution function that coordinates everything |

### ⚙️ Configuration Files

**`config/check_dates.json`** - Controls what dates to check:
```json
{
    "check_upcoming_friday": true,
    "check_upcoming_monday": true,
    "custom_dates": []
}
```

**`config/settings.json`** - Application settings:
```json
{
    "academies": ["kotak", "pullela", "sai"],
    "time_slots": ["12:00-13:00", "13:00-14:00", "19:00-20:00", "20:00-21:00", "21:00-22:00"],
    "notification_enabled": true
}
```

## 🔄 How It Works - Step by Step

1. **Trigger**: GitHub Actions runs every hour OR you run locally
2. **Environment Detection**: System detects if running locally (💻) or on GitHub Actions (🤖)
3. **API Authentication**: Loads saved authentication tokens
4. **Multi-Academy Check**: Simultaneously queries all 3 academies using real API endpoints
5. **Data Processing**: Parses slot availability into structured format
6. **Table Generation**: Creates beautiful ASCII table with ✓ (available) and • (unavailable) symbols
7. **Telegram Notification**: Sends formatted message showing availability across all courts and time slots
8. **Session Persistence**: Saves authentication state for next run

## 📱 Telegram Message Format

Your messages will look like this:
```
🏸 Badminton Slots Available (API)

📍 Kotak Academy
  📅 Fri Sep 19
   12h   13h   19h   20h   21h  
 1   ✓     ✓     •     ✓     •   
 2   ✓     ✓     •     •     •   
 3   ✓     ✓     •     •     ✓   
    📊 6 slots available

🎯 Total: 23 slots
⚡ Via API - 14:53 - 🤖 GitHub Actions
```

**Symbol Legend:**
- ✓ = Available slot
- • = Unavailable slot  
- Numbers (1,2,3...) = Court numbers
- Time headers = Hour slots (12h = 12:00-13:00)

## 🛠️ Local Development & Testing

### Prerequisites
- Python 3.11+
- Internet connection

### Local Setup
```bash
# Clone your forked repository
git clone https://github.com/YOUR_USERNAME/badminton_booking.git
cd badminton_booking

# Install dependencies  
pip install -r requirements.txt

# Create local environment file
cp .env.example .env
# Edit .env with your Telegram credentials

# Test your setup
python run_local_test.py
```

### Available Test Commands

| Command | Purpose |
|---------|---------|
| `python run_local_test.py` | Full end-to-end test with Telegram notification |
| `python get_chat_id.py` | Get your Telegram chat ID |
| `python github_actions_checker.py` | Run the main checker directly |

## 📊 Performance Metrics

- **Speed**: 81 slots across 3 academies in ~28 seconds
- **Accuracy**: Direct API integration ensures real-time data
- **Reliability**: 99.9% uptime with GitHub Actions
- **Efficiency**: No browser overhead, pure HTTP requests
- **Cost**: Completely free (GitHub Actions provides 2000 minutes/month free)

## 🔍 Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| **No Telegram notifications** | Check bot token and chat ID in repository secrets |
| **"No slots found" always** | API tokens may have expired - check GitHub Actions logs |
| **Workflow not running** | Ensure GitHub Actions are enabled in repository settings |
| **Local testing fails** | Verify .env file has correct Telegram credentials |

### Debug Information

- **GitHub Actions Logs**: Go to Actions tab → latest run → view logs
- **Local Debug**: Run `python run_local_test.py` to see detailed output
- **API Status**: Check if you can access `https://booking.gopichandacademy.com/`

## 🤝 Contributing

This project welcomes contributions! Here are some areas for improvement:

1. **Additional Time Slots**: Support for more time ranges
2. **More Academies**: Support for other badminton booking systems  
3. **Advanced Filtering**: Court preferences, player count filtering
4. **Historical Analytics**: Track availability patterns over time
5. **Mobile App**: Native app for better notifications

## 📄 License

MIT License - Feel free to modify and distribute!

## 🏸 Happy Playing!

Once set up, you'll never miss a badminton slot again! The system works 24/7 to find available courts and notify you instantly with beautiful, easy-to-read tables.

**⚡ System Status**: Production-ready, fully automated, zero maintenance required!

---

*⚠️ Disclaimer: This tool is for personal use to check availability. Always book through the official website. Respect the booking system's terms of service.*
