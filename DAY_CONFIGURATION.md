# Day Configuration Guide

## Overview
You can now configure which days of the week the badminton checker should look for court availability. By default, it checks for **Friday** and **Monday**, but you can customize this to check any combination of days.

## Configuration Location
The day configuration is stored in `config/settings.json` under the `check_days` section:

```json
{
    "check_days": {
        "monday": true,
        "tuesday": false,
        "wednesday": false,
        "thursday": false,
        "friday": true,
        "saturday": false,
        "sunday": false
    }
}
```

## How It Works
- **`true`**: The checker will look for the next upcoming occurrence of this day
- **`false`**: The checker will skip this day entirely
- The system automatically calculates the next upcoming dates for enabled days
- Dates are sorted chronologically in the results

## Examples

### Default Configuration (Friday & Monday)
```json
"check_days": {
    "monday": true,
    "tuesday": false,
    "wednesday": false,
    "thursday": false,
    "friday": true,
    "saturday": false,
    "sunday": false
}
```
**Result**: Checks next Friday and next Monday

### Weekend Only
```json
"check_days": {
    "monday": false,
    "tuesday": false,
    "wednesday": false,
    "thursday": false,
    "friday": false,
    "saturday": true,
    "sunday": true
}
```
**Result**: Checks next Saturday and next Sunday

### Weekdays Only
```json
"check_days": {
    "monday": true,
    "tuesday": true,
    "wednesday": true,
    "thursday": true,
    "friday": true,
    "saturday": false,
    "sunday": false
}
```
**Result**: Checks next Monday, Tuesday, Wednesday, Thursday, and Friday

### Single Day
```json
"check_days": {
    "monday": false,
    "tuesday": false,
    "wednesday": true,
    "thursday": false,
    "friday": false,
    "saturday": false,
    "sunday": false
}
```
**Result**: Checks only next Wednesday

## Important Notes
1. **At least one day must be enabled** - if all days are set to `false`, the system defaults to Friday and Monday
2. **"Next" occurrence**: If today is the configured day, it will check the following week's occurrence
3. **IST timezone**: All date calculations use Indian Standard Time (IST)
4. **Automatic sorting**: Results are always sorted by date, regardless of configuration order

## Testing Your Configuration
You can test your day configuration by running:
```bash
python -c "from src.checker_helpers import get_check_dates; import json; print(json.dumps(get_check_dates(), indent=2))"
```

This will show you which dates the system will check based on your current configuration.

## Telegram Message Format
The Telegram message will show all configured days in chronological order, for example:
- **Default**: "📅 Checking dates: Mon Sep 22 & Fri Sep 26"  
- **Weekends**: "📅 Checking dates: Sat Sep 20 & Sun Sep 21"
- **All weekdays**: "📅 Checking dates: Mon Sep 22 & Tue Sep 23 & Wed Sep 24 & Thu Sep 25 & Fri Sep 26"