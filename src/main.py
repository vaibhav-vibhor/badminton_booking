#!/usr/bin/env python3
"""
Badminton Booking Slot Checker
Main script that coordinates all components to check for available badminton slots
across multiple academies and send notifications when slots are found.
"""

import asyncio
import logging
import sys
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    async_playwright = None

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from config_handler import get_config, ConfigHandler
from login_handler import LoginHandler
from booking_checker import BookingChecker
from academy_checker import AcademyChecker
from notification_handler import NotificationHandler
from slot_analyzer import SlotAnalyzer, DateTimeUtils, DataPersistence

class BadmintonSlotChecker:
    """
    Main class that orchestrates the badminton slot checking process
    """
    
    def __init__(self):
        self.config = get_config()
        self.setup_logging()
        
        # Initialize components
        self.login_handler = LoginHandler(self.config.phone_number)
        self.booking_checker = BookingChecker()
        self.academy_checker = AcademyChecker()
        self.notification_handler = NotificationHandler(
            self.config.telegram_bot_token,
            self.config.telegram_chat_id,
            self._get_email_config()
        )
        
        # Track session state
        self.session_active = False
        self.check_count = 0
        
    def setup_logging(self):
        """Set up logging configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Configure logging
        log_filename = f"logs/badminton_checker_{datetime.now().strftime('%Y%m%d')}.log"
        
        handlers = []
        
        # File handler
        if self.config.settings.get("logging", {}).get("file_logging", True):
            file_handler = logging.FileHandler(log_filename, encoding='utf-8')
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            handlers.append(file_handler)
        
        # Console handler
        if self.config.settings.get("logging", {}).get("console_logging", True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            handlers.append(console_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            handlers=handlers,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set playwright to warning level to reduce noise
        logging.getLogger('playwright').setLevel(logging.WARNING)
        
        logging.info("Badminton Slot Checker initialized")
    
    def _get_email_config(self) -> Dict[str, str]:
        """Get email configuration if available"""
        if all([self.config.email_smtp_server, self.config.email_username, self.config.email_password]):
            return {
                "smtp_server": self.config.email_smtp_server,
                "smtp_port": self.config.email_smtp_port,
                "username": self.config.email_username,
                "password": self.config.email_password
            }
        return {}
    
    async def run_single_check(self) -> Dict[str, Any]:
        """
        Run a single check cycle for available slots
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise RuntimeError("Playwright is not installed. Please run: pip install playwright && playwright install chromium")
            
        check_start_time = datetime.now()
        check_result = {
            "timestamp": check_start_time.isoformat(),
            "success": False,
            "slots_found": 0,
            "academies_checked": [],
            "error": None,
            "duration_seconds": 0
        }
        
        try:
            logging.info(f"Starting check #{self.check_count + 1}")
            
            # Validate dates
            target_dates = self.config.dates_to_check
            valid_dates = [date for date in target_dates if DateTimeUtils.is_valid_date(date)]
            
            if not valid_dates:
                raise ValueError("No valid future dates configured for checking")
            
            if len(valid_dates) != len(target_dates):
                logging.warning(f"Filtered out {len(target_dates) - len(valid_dates)} past dates")
            
            logging.info(f"Checking dates: {', '.join(valid_dates)}")
            
            # Get academies to check
            academies_to_check = self.config.get_academies_to_check()
            academies = {k: v for k, v in self.config.academies.items() if k in academies_to_check}
            
            if not academies:
                raise ValueError("No academies configured for checking")
            
            logging.info(f"Checking academies: {', '.join(academies.keys())}")
            
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.config.browser_settings["headless"],
                    args=['--no-sandbox', '--disable-dev-shm-usage']  # For GitHub Actions
                )
                
                context = await browser.new_context(
                    viewport=self.config.browser_settings.get("viewport"),
                    user_agent=self.config.browser_settings.get("user_agent")
                )
                
                page = await context.new_page()
                page.set_default_timeout(self.config.browser_settings["timeout"])
                
                try:
                    # Login if not already logged in
                    if not self.session_active:
                        logging.info("Attempting to log in...")
                        login_success = await self.login_handler.login(page)
                        
                        if not login_success:
                            raise Exception("Login failed")
                        
                        self.session_active = True
                        logging.info("Login successful")
                    
                    # Navigate to badminton section
                    badminton_url = self.config.urls.get("badminton_section", "https://booking.gopichandacademy.com/venuePage/1")
                    await page.goto(badminton_url, wait_until="domcontentloaded")
                    
                    # Check for available slots
                    logging.info("Checking for available slots...")
                    
                    available_slots = await self.booking_checker.get_all_available_slots(
                        page,
                        academies,
                        valid_dates,
                        self.config.rate_limiting
                    )
                    
                    # Remove duplicates
                    available_slots = self.booking_checker.remove_duplicate_slots(available_slots)
                    
                    # Filter by preferences
                    filtered_slots = self.booking_checker.filter_slots_by_preferences(
                        available_slots,
                        self.config.time_preferences,
                        self.config.court_preferences
                    )
                    
                    # Update check result
                    check_result.update({
                        "success": True,
                        "slots_found": len(filtered_slots),
                        "academies_checked": list(academies.keys()),
                        "total_raw_slots": len(available_slots)
                    })
                    
                    # Log results
                    if filtered_slots:
                        logging.info(f"Found {len(filtered_slots)} available slots matching preferences")
                        
                        # Send notifications
                        await self.notification_handler.send_slot_notifications(
                            filtered_slots,
                            self.config.notification_settings
                        )
                    else:
                        logging.info("No available slots found matching preferences")
                    
                    # Save slots to file for analysis
                    DataPersistence.save_slots_to_file(filtered_slots)
                    
                    # Clean up old notifications periodically
                    if self.check_count % 10 == 0:  # Every 10 checks
                        self.notification_handler.cleanup_old_notifications()
                    
                    return {
                        "success": True,
                        "slots_found": filtered_slots,
                        "raw_slots": available_slots,
                        "stats": self.booking_checker.get_summary_stats(filtered_slots)
                    }
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Error during slot check: {error_msg}")
            logging.debug(traceback.format_exc())
            
            check_result["error"] = error_msg
            
            # Send error notification
            try:
                await self.notification_handler.send_error_notification(error_msg)
            except:
                logging.error("Failed to send error notification")
            
            return {
                "success": False,
                "error": error_msg,
                "slots_found": [],
                "raw_slots": [],
                "stats": {}
            }
        
        finally:
            # Update check result duration
            check_result["duration_seconds"] = (datetime.now() - check_start_time).total_seconds()
            
            # Save check history
            DataPersistence.save_check_history(check_result)
            
            self.check_count += 1
    
    async def run_continuous(self):
        """
        Run the checker continuously based on configured interval
        """
        logging.info("Starting continuous badminton slot monitoring...")
        
        # Send startup notification
        try:
            await self.notification_handler.send_startup_notification()
        except:
            logging.warning("Failed to send startup notification")
        
        while True:
            try:
                result = await self.run_single_check()
                
                if result["success"]:
                    slots_count = len(result.get("slots_found", []))
                    logging.info(f"Check completed successfully. Found {slots_count} slots.")
                else:
                    logging.error(f"Check failed: {result.get('error', 'Unknown error')}")
                
                # Wait for next check
                interval_minutes = self.config.settings.get("check_interval_minutes", 15)
                logging.info(f"Waiting {interval_minutes} minutes until next check...")
                await asyncio.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                logging.info("Received interrupt signal, shutting down gracefully...")
                break
            except Exception as e:
                logging.error(f"Unexpected error in continuous mode: {str(e)}")
                logging.debug(traceback.format_exc())
                
                # Wait before retrying
                await asyncio.sleep(300)  # 5 minutes
    
    async def test_system(self) -> bool:
        """
        Test all components of the system
        """
        logging.info("Running system tests...")
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Configuration
        total_tests += 1
        try:
            config_test = all([
                self.config.phone_number,
                self.config.telegram_bot_token,
                self.config.telegram_chat_id,
                len(self.config.dates_to_check) > 0
            ])
            
            if config_test:
                logging.info("✅ Configuration test passed")
                tests_passed += 1
            else:
                logging.error("❌ Configuration test failed")
        except Exception as e:
            logging.error(f"❌ Configuration test failed: {str(e)}")
        
        # Test 2: Notification system
        total_tests += 1
        try:
            notification_success = await self.notification_handler.test_notification_system()
            if notification_success:
                logging.info("✅ Notification test passed")
                tests_passed += 1
            else:
                logging.error("❌ Notification test failed")
        except Exception as e:
            logging.error(f"❌ Notification test failed: {str(e)}")
        
        # Test 3: Browser automation
        total_tests += 1
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Try to access the main website
                await page.goto("https://booking.gopichandacademy.com/", timeout=10000)
                
                if "gopichandacademy" in page.url:
                    logging.info("✅ Browser automation test passed")
                    tests_passed += 1
                else:
                    logging.error("❌ Browser automation test failed")
                
                await browser.close()
        except Exception as e:
            logging.error(f"❌ Browser automation test failed: {str(e)}")
        
        # Test summary
        success_rate = (tests_passed / total_tests) * 100
        logging.info(f"System test results: {tests_passed}/{total_tests} passed ({success_rate:.1f}%)")
        
        return tests_passed == total_tests


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Badminton Booking Slot Checker")
    parser.add_argument("--mode", choices=["single", "continuous", "test"], default="single",
                       help="Running mode: single check, continuous monitoring, or system test")
    parser.add_argument("--config-dir", default="config", 
                       help="Configuration directory path")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    try:
        # Override config directory if specified
        if args.config_dir != "config":
            os.environ["CONFIG_DIR"] = args.config_dir
        
        # Initialize checker
        checker = BadmintonSlotChecker()
        
        # Override log level if verbose
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
            logging.info("Verbose logging enabled")
        
        # Run based on mode
        if args.mode == "test":
            success = await checker.test_system()
            sys.exit(0 if success else 1)
        elif args.mode == "single":
            result = await checker.run_single_check()
            if result["success"]:
                slots_count = len(result.get("slots_found", []))
                print(f"Check completed. Found {slots_count} available slots.")
                
                # Print summary if slots found
                if slots_count > 0:
                    stats = result.get("stats", {})
                    print(f"Total slots: {stats.get('total', 0)}")
                    print(f"By academy: {stats.get('by_academy', {})}")
            else:
                print(f"Check failed: {result.get('error', 'Unknown error')}")
                sys.exit(1)
        elif args.mode == "continuous":
            await checker.run_continuous()
        
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        logging.debug(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # Ensure we can import from the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Run the main function
    asyncio.run(main())
