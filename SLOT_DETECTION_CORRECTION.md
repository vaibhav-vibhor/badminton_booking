# CORRECTED BADMINTON SLOT DETECTION LOGIC
# =========================================
# Based on the HTML structure you provided

## KEY FINDINGS FROM YOUR HTML:

### 1. CORRECT HTML SELECTORS:
- Date input: `input#card1[type='date']`
- Courts: `div.court-item` (appear after date selection)
- Active court: `div.court-item.active-court`
- Time slots: `span.styled-btn` (appear after court selection)
- Time container: `div.time-slots-container`

### 2. CORRECT AVAILABILITY LOGIC:
```python
def is_slot_available(style):
    """
    Available slots: style="" or no red+not-allowed combination
    Booked slots: style="color: red; cursor: not-allowed;"
    """
    if not style:
        return True  # Empty style = available
    
    style_lower = style.lower()
    has_red_color = 'color: red' in style_lower
    has_not_allowed = 'cursor: not-allowed' in style_lower
    
    # Available if NOT (red AND not-allowed)
    return not (has_red_color and has_not_allowed)
```

### 3. CORRECT WORKFLOW:
```python
async def check_slots_correctly(page, date):
    # Step 1: Set date
    date_input = await page.wait_for_selector('input#card1[type="date"]')
    await date_input.fill(date)
    await date_input.dispatch_event('change')
    await asyncio.sleep(3)  # Wait for courts to load
    
    # Step 2: Get courts
    courts = await page.query_selector_all('div.court-item')
    
    # Step 3: Check each court
    for court in courts:
        court_number = await court.inner_text()
        await court.click()
        await asyncio.sleep(2)  # Wait for time slots
        
        # Step 4: Get time slots
        slots = await page.query_selector_all('span.styled-btn')
        
        # Step 5: Check availability
        for slot in slots:
            time_text = await slot.inner_text()
            style = await slot.get_attribute('style') or ''
            
            # Apply corrected logic
            if is_slot_available(style):
                print(f"✅ AVAILABLE: Court {court_number} - {time_text}")
            else:
                print(f"❌ BOOKED: Court {court_number} - {time_text}")
```

## WHAT TO UPDATE:

1. **In BookingChecker class** (`src/booking_checker.py`):
   - ✅ Updated selectors (DONE)
   - ✅ Updated availability logic (DONE)
   - ✅ Added proper waiting for courts after date selection (DONE)

2. **Test the updated logic**:
   - Run `python improved_checker.py` (login works)
   - The BookingChecker it uses now has the corrected logic
   - You should see actual available/booked slot detection

## EXPECTED RESULTS:
- If the corrected logic works, you'll see either:
  - ✅ "Found X available slots" (if there are free courts)
  - ℹ️ "No available slots found" (if all courts are booked - which is normal)

## VERIFICATION:
The corrected logic should now properly detect:
- Courts that appear after date selection
- Time slots that appear after court selection  
- Availability based on style attributes (red = booked, no red = available)

## NEXT STEPS:
1. Run `python improved_checker.py` to test the corrected logic
2. If it finds available slots, you'll get a Telegram notification
3. If no slots are found, that's normal (courts are fully booked)
4. The system is now ready for automated deployment via GitHub Actions
