# 🏸 Badminton Booking Slot Checker

An automated system that monitors badminton court availability across multiple Gopichand Academy locations and sends instant notifications when your preferred slots become available. **Now automatically focuses on upcoming Fridays and Mondays!**

## 🚀 Features

- **Multi-Academy Monitoring**: Checks all 3 Gopichand Academy locations simultaneously
  - Kotak Pullela Gopichand Badminton Academy
  - Pullela Gopichand Badminton Academy  
  - SAI Gopichand Pullela Gopichand Badminton Academy

- **Friday & Monday Focus**: Automatically checks upcoming Fridays and Mondays (next 2 weeks)
- **Smart Session Management**: Maintains login session across page navigation
- **Instant Notifications**: Real-time Telegram alerts when slots become available  
- **Easy Execution**: Simple one-click batch file or Python script
- **Automated Login**: Handles phone number + OTP authentication
- **Error Handling**: Robust error recovery and notification system

## 📋 Prerequisites

1. **Phone number** registered with Gopichand Academy booking system
2. **Telegram account** for receiving notifications
3. **GitHub account** for free hosting (optional for manual runs)

## 🎯 Quick Start - Friday & Monday Checker

The easiest way to check upcoming Friday and Monday availability:

### Local Execution (Recommended)

1. **Clone/Download** this repository
2. **Create `.env` file** in the root directory:
```env
PHONE_NUMBER=your_phone_number
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

3. **Run the checker**:
   - **Windows**: Double-click `run_friday_monday_checker.bat`
   - **Command line**: `python friday_monday_checker.py`

4. **Manual OTP entry**: Enter OTP code when prompted in the browser

The script will automatically:
- ✅ Check next 2 upcoming Fridays and Mondays
- ✅ Login and maintain session across all academies
- ✅ Send detailed Telegram notification with all available slots
- ✅ Display results in console with clear formatting

## 🛠️ Setup Instructions

### Step 1: Create Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow prompts to create your bot
4. Save the **Bot Token** (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
5. Start a chat with your new bot and send any message
6. Get your Chat ID by visiting: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
7. Find your **Chat ID** in the response (looks like `123456789`)

### Step 2: Fork and Configure Repository

1. **Fork this repository** to your GitHub account
2. Go to your forked repository
3. Navigate to **Settings** → **Secrets and variables** → **Actions**
4. Click **New repository secret** and add these secrets:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `PHONE_NUMBER` | Your registered phone number | `9876543210` |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather | `123456789:ABCdef...` |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID | `123456789` |

### Step 3: Configure Dates and Preferences

1. Edit `config/check_dates.json` in your repository:

```json
{
    "dates_to_check": [
        "2025-09-13",
        "2025-09-14", 
        "2025-09-15"
    ],
    "time_preferences": {
        "preferred": [
            "18:00-19:00",
            "19:00-20:00", 
            "20:00-21:00"
        ],
        "acceptable": [
            "17:00-18:00",
            "21:00-22:00"
        ],
        "notify_all": false
    },
    "court_preferences": {
        "preferred_courts": [1, 2, 3, 4, 5],
        "check_all_courts": true
    },
    "academies_to_check": ["kotak", "pullela", "sai"],
    "notification_settings": {
        "notify_immediately": true,
        "batch_notifications": false,
        "max_notifications_per_run": 10
    }
}
```

### Step 4: Enable GitHub Actions

1. Go to **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. The checker will now run automatically every 15 minutes!

## 🎯 Usage

### Automatic Monitoring

Once set up, the system runs automatically:
- **Every 15 minutes** during peak hours (9 AM - 11 PM IST)
- **Checks all configured academies** for your preferred dates
- **Sends Telegram notifications** when slots are found
- **Prevents duplicate alerts** for the same slots

### Manual Execution

You can also trigger manual checks:

1. Go to **Actions** tab in your repository
2. Click on **"Badminton Slot Checker"** workflow
3. Click **"Run workflow"** button
4. Choose options:
   - **Check mode**: `single` (one-time check) or `test` (system test)
   - **Specific date**: Override configured dates (optional)
   - **Verbose logging**: Enable detailed logs for debugging

### Local Testing

To run locally for testing:

```bash
# Clone your repository
git clone https://github.com/YOUR_USERNAME/BadmintonBooking.git
cd BadmintonBooking

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# PHONE_NUMBER=your_phone_number
# TELEGRAM_BOT_TOKEN=your_bot_token  
# TELEGRAM_CHAT_ID=your_chat_id

# Test the system
cd src
python main.py --mode test

# Run single check
python main.py --mode single --verbose
```

## 📱 Notification Examples

### Single Slot Found
```
🏸 ⭐ BADMINTON SLOT AVAILABLE!

🏛️ Academy: Kotak Pullela Gopichand
📅 Date: 15 Sep 2025 (Monday)
🏟️ Court: Court 2
⏰ Time: 18:00-19:00

🔗 Book now: https://booking.gopichandacademy.com/venue-details/1

⚡ Book quickly as slots fill up fast!
```

### Multiple Slots Found
```
🏸 5 BADMINTON SLOTS AVAILABLE!
⭐ 3 preferred slots found

🏛️ Kotak (3 slots):
  ⭐ 15 Sep • Court 2 • 18:00-19:00
  ⭐ 15 Sep • Court 3 • 19:00-20:00
  16 Sep • Court 1 • 21:00-22:00

🏛️ Pullela (2 slots):
  ⭐ 16 Sep • Court 4 • 20:00-21:00
  17 Sep • Court 2 • 17:00-18:00

🔗 Book at: https://booking.gopichandacademy.com/
⚡ Book quickly as slots fill up fast!
```

## ⚙️ Configuration Options

### Date Configuration
- **dates_to_check**: List of dates in YYYY-MM-DD format
- Update regularly or use date ranges

### Time Preferences
- **preferred**: High-priority time slots (get ⭐ in notifications)
- **acceptable**: Secondary time slots
- **notify_all**: Set to `true` to get notified about any available slot

### Court Preferences  
- **preferred_courts**: List of court numbers [1, 2, 3, etc.]
- **check_all_courts**: Set to `false` to only check preferred courts

### Academy Selection
- **academies_to_check**: `["kotak", "pullela", "sai"]` or `["all"]`
- Can exclude academies you don't want to check

### Notification Settings
- **notify_immediately**: Send notifications as soon as slots are found
- **batch_notifications**: Group multiple slots in one message
- **max_notifications_per_run**: Limit notifications per check cycle

## 🔧 Troubleshooting

### Common Issues

**1. No notifications received**
- Verify Telegram bot token and chat ID in repository secrets
- Check that you've sent a message to your bot first
- Look at GitHub Actions logs for errors

**2. Login failures**
- Ensure phone number is correctly formatted (without +91)
- Check if OTP is required (current limitation - needs manual intervention)

**3. GitHub Actions not running**
- Verify Actions are enabled in repository settings
- Check that secrets are properly configured
- Repository must have recent commits (GitHub disables inactive workflows)

**4. Wrong dates being checked**
- Update `config/check_dates.json` with future dates
- Past dates are automatically filtered out

### Advanced Troubleshooting

**Enable verbose logging:**
```bash
python main.py --mode single --verbose
```

**Test individual components:**
```bash
python main.py --mode test
```

**Check logs in GitHub Actions:**
1. Go to Actions tab
2. Click on latest workflow run
3. Expand "Run badminton slot checker" step
4. Review detailed logs

### OTP Handling Limitation

Currently, OTP must be entered manually for first-time login. To work around this:

1. Run the script locally once to establish a session
2. The session cookies will be saved for future runs
3. GitHub Actions will use the established session

*Future enhancement: Automated OTP handling via SMS API or email parsing*

## 📊 Monitoring and Analytics

### Check History
- All checks are logged to `data/check_history.json`
- Includes success/failure rates, slots found, errors

### Slot Data
- Latest slots saved to `data/latest_slots.json`  
- Historical data for analysis

### GitHub Actions Insights
- View run history and success rates
- Download logs and slot data as artifacts
- Weekly summary notifications

## 🚨 Rate Limiting and Best Practices

The system implements smart rate limiting:
- **2 second delay** between requests
- **5 second delay** between academies  
- **1 second delay** between courts
- **15 minute interval** between full checks

**Important:** 
- Don't reduce delays too much (risk of being blocked)
- Don't run multiple instances simultaneously  
- Respect the booking website's terms of service

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

1. **OTP Automation**: SMS API integration or email parsing
2. **Additional Academies**: Support for other booking systems
3. **Web Dashboard**: Visual interface for configuration
4. **Smart Scheduling**: ML-based optimal check timing
5. **Mobile App**: Native mobile notifications

## 📄 License

This project is for educational purposes. Please respect the terms of service of the booking website and use responsibly.

## 🙋‍♂️ Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review GitHub Actions logs for error details
3. Create an issue in this repository with:
   - Error messages from logs
   - Your configuration (without credentials)
   - Steps to reproduce the problem

## 🏸 Happy Playing!

Once set up, you'll never miss a badminton slot again! The system works 24/7 to find available courts and notify you instantly via Telegram.

---

**⚠️ Disclaimer**: This tool is for personal use to check availability. Always book through the official website. Respect the booking system's terms of service and don't attempt to automate actual bookings.
