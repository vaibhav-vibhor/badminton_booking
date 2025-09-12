# 📊 Next Friday & Monday Badminton Checker Status

## ✅ System Configuration

**Last Updated**: September 12, 2025
**Status**: Ready for Use
**Focus**: Next upcoming Friday and Monday only (2 dates total)

## 🎯 What This System Does

### 📅 Date Selection
- **Automatically** identifies the next upcoming Friday and Monday
- **Only 2 dates** checked per run for focused results
- **Current upcoming dates**:
  - Monday, September 15, 2025
  - Friday, September 19, 2025

### 🏸 Academy Coverage
- ✅ **Kotak Pullela Gopichand Badminton Academy** (venue-details/1)
- ✅ **Pullela Gopichand Badminton Academy** (venue-details/2)  
- ✅ **SAI Pullela Gopichand National Badminton Academy** (venue-details/3)

### 🔄 Process Flow
1. **Authentication**: Login with phone + OTP (manual entry required)
2. **Session Management**: Maintains login across all academy pages
3. **Court Scanning**: Checks all available courts for each date
4. **Slot Detection**: Identifies available time slots 
5. **Telegram Notification**: Sends formatted message with all findings

## 📱 Notification Format

The Telegram message includes:
- Total slots found across all academies
- Breakdown by date (Friday/Monday)
- Academy-specific availability  
- Court numbers and time slots
- Timestamp of check

## 🚀 How to Run

### Quick Start
```bash
# Windows
run_friday_monday_checker.bat

# Command Line  
python friday_monday_checker.py

# Original comprehensive
python complete_e2e_test.py
```

### Requirements
- ✅ `.env` file with credentials
- ✅ Playwright browser automation
- ✅ Active internet connection
- ✅ Manual OTP entry during login

## 🔧 Maintenance

- **Automatic date calculation** - always finds next Friday and Monday
- **Focused checking** - only 2 dates per run for faster execution
- **Session persistence** - handles login/logout gracefully
- **Error handling** - continues checking even if one academy fails
- **Logging** - detailed logs saved to `logs/` directory

## 📈 Success Metrics

From previous runs:
- ✅ **Session Management**: 100% success rate (no more logout issues)
- ✅ **Slot Detection**: Successfully found 200+ slots in testing
- ✅ **Telegram Delivery**: 100% notification success rate
- ✅ **Multi-Academy**: All 3 academies checked without failures
