# 🏸 GitHub Actions Setup Guide

## Simple 5-Step Setup Process

### Step 1: Fork This Repository
1. Click the "Fork" button at the top of this page
2. This creates your own copy of the project

### Step 2: Set Up Your Secrets
1. Go to your forked repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these 3 secrets:

| Secret Name | Value | Where to Get It |
|-------------|--------|-----------------|
| `PHONE_NUMBER` | Your phone number | Your registered Gopichand Academy phone |
| `TELEGRAM_BOT_TOKEN` | Bot token | Create bot with @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Your chat ID | Message your bot, then visit bot API |

#### Getting Telegram Bot Token & Chat ID:
1. **Create Bot**: Message @BotFather on Telegram
   - Send `/newbot`
   - Choose a name
   - Get your `TELEGRAM_BOT_TOKEN` (save this)

2. **Get Chat ID**: 
   - Start a chat with your new bot
   - Send any message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `TELEGRAM_CHAT_ID` in the response

### Step 3: Initial Login (One Time Setup)
Since GitHub Actions can't handle OTP, you need to login once locally:

1. **Run locally first** (on your computer):
   ```bash
   python github_actions_checker.py
   ```
   
2. **Complete the manual login** when browser opens
3. **Session will be saved** for GitHub Actions to use

### Step 4: Enable GitHub Actions
1. Go to **Actions** tab in your repository
2. Click **"I understand my workflows, go ahead and enable them"**
3. Your checker will now run **automatically every hour**!

### Step 5: Test It
1. Go to **Actions** → **Badminton Slot Checker**
2. Click **Run workflow** to test manually
3. Check your Telegram for the results!

---

## How It Works

### Automatic Schedule
- ✅ **Runs every hour** at 5 minutes past the hour
- ✅ **Checks Friday & Monday** slots only
- ✅ **All 3 academies** checked automatically
- ✅ **Telegram notifications** sent with results

### Session Management
- ✅ **Login once locally** = works for weeks in GitHub Actions
- ✅ **Session automatically restored** between runs
- ✅ **Smart expiry detection** - notifies you when re-login needed
- ✅ **Manual refresh option** via GitHub Actions UI

### Free Usage
- ✅ **2,000 minutes/month free** (way more than needed)
- ✅ **No credit card required**
- ✅ **No maintenance needed**

---

## When Session Expires (Every Few Weeks)

You'll get a Telegram message saying "Manual Login Required". Then:

**Option 1 - GitHub Actions UI:**
1. Go to **Actions** → **Badminton Slot Checker**
2. Click **Run workflow**
3. Check **"Force fresh login"**
4. You'll get OTP notification on Telegram

**Option 2 - Run Locally:**
```bash
python github_actions_checker.py
```
Complete login manually, session saves automatically.

---

## Troubleshooting

### "No session data found"
- Run the script locally once to establish session

### "Session too old" 
- Normal after ~24 hours, login locally or use "Force fresh login"

### "Import errors"
- Make sure `requirements.txt` is properly committed

### Not receiving messages
- Check your `TELEGRAM_CHAT_ID` is correct
- Make sure you started a chat with your bot

---

## What You'll Receive

### When Slots Are Available:
```
🏸 SLOTS AVAILABLE!

🎯 Found 5 available slots!

📅 Monday, September 15
   🏟️ Kotak
      🏸 Court 1 at 18:00-19:00
      🏸 Court 2 at 19:00-20:00

📅 Friday, September 19  
   🏟️ SAI
      🏸 Court 5 at 20:00-21:00

🔗 Book Now
⏰ Checked at 14:05 IST
```

### When No Slots:
```
🏸 Badminton Checker Update

😔 No slots available

📅 Checked: Monday Sep 15 & Friday Sep 19
🏟️ All 3 academies checked
⏰ Next check in 1 hour

All courts are currently booked.
```

---

## Summary

1. **Fork** repository ✅
2. **Add 3 secrets** (phone, bot token, chat ID) ✅  
3. **Run locally once** (for initial login) ✅
4. **Enable Actions** ✅
5. **Enjoy hourly updates!** 🎉

**Total setup time: ~10 minutes**
**Maintenance needed: Re-login every few weeks**
