import asyncio
import logging
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests

class NotificationHandler:
    """
    Handles sending notifications via Telegram and email
    """
    
    def __init__(self, telegram_bot_token: str, telegram_chat_id: str, email_config: Optional[Dict] = None):
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id
        self.email_config = email_config
        self.sent_notifications_file = "data/sent_notifications.json"
        self.sent_notifications = self._load_sent_notifications()
        
    def _load_sent_notifications(self) -> Dict[str, str]:
        """Load previously sent notifications to avoid duplicates"""
        try:
            with open(self.sent_notifications_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_sent_notifications(self):
        """Save sent notifications to file"""
        try:
            import os
            os.makedirs(os.path.dirname(self.sent_notifications_file), exist_ok=True)
            with open(self.sent_notifications_file, 'w') as f:
                json.dump(self.sent_notifications, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving sent notifications: {str(e)}")
    
    def _generate_slot_key(self, slot: Dict[str, Any]) -> str:
        """Generate unique key for a slot to track notifications"""
        return f"{slot['academy']}_{slot['date']}_{slot['court']}_{slot['time']}"
    
    async def send_slot_notifications(self, available_slots: List[Dict[str, Any]], notification_settings: Dict[str, Any]):
        """Send notifications for available slots"""
        if not available_slots:
            logging.info("No available slots to notify about")
            return
        
        # Filter out already notified slots
        new_slots = []
        for slot in available_slots:
            slot_key = self._generate_slot_key(slot)
            if slot_key not in self.sent_notifications:
                new_slots.append(slot)
        
        if not new_slots:
            logging.info("All available slots have already been notified")
            return
        
        # Limit notifications per run
        max_notifications = notification_settings.get("max_notifications_per_run", 10)
        slots_to_notify = new_slots[:max_notifications]
        
        if notification_settings.get("batch_notifications", False):
            # Send all slots in one message
            await self._send_batch_notification(slots_to_notify)
        else:
            # Send individual notifications
            await self._send_individual_notifications(slots_to_notify)
        
        # Mark slots as notified
        for slot in slots_to_notify:
            slot_key = self._generate_slot_key(slot)
            self.sent_notifications[slot_key] = datetime.now().isoformat()
        
        self._save_sent_notifications()
        
        logging.info(f"Sent {len(slots_to_notify)} slot notifications")
    
    async def _send_individual_notifications(self, slots: List[Dict[str, Any]]):
        """Send individual notification for each slot"""
        for slot in slots:
            message = self._format_slot_notification(slot)
            await self._send_telegram_message(message)
            
            # Small delay between messages to avoid rate limiting
            await asyncio.sleep(1)
    
    async def _send_batch_notification(self, slots: List[Dict[str, Any]]):
        """Send all slots in one batch message"""
        if len(slots) == 1:
            message = self._format_slot_notification(slots[0])
        else:
            message = self._format_batch_notification(slots)
        
        await self._send_telegram_message(message)
    
    def _format_slot_notification(self, slot: Dict[str, Any]) -> str:
        """Format single slot for notification"""
        # Format date nicely
        try:
            date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
            formatted_date = date_obj.strftime("%d %b %Y (%A)")
        except:
            formatted_date = slot["date"]
        
        preference_emoji = "⭐" if slot.get("preference_level") == "preferred" else ""
        
        message = (
            f"🏸 {preference_emoji} BADMINTON SLOT AVAILABLE!\n\n"
            f"🏛️ Academy: {slot['academy']}\n"
            f"📅 Date: {formatted_date}\n"
            f"🏟️ Court: {slot['court']}\n"
            f"⏰ Time: {slot['time']}\n\n"
            f"🔗 Book now: {slot['booking_url']}\n\n"
            f"⚡ Book quickly as slots fill up fast!"
        )
        
        return message
    
    def _format_batch_notification(self, slots: List[Dict[str, Any]]) -> str:
        """Format multiple slots for batch notification"""
        total_slots = len(slots)
        preferred_count = sum(1 for slot in slots if slot.get("preference_level") == "preferred")
        
        header = (
            f"🏸 {total_slots} BADMINTON SLOTS AVAILABLE!\n"
            f"⭐ {preferred_count} preferred slots found\n\n"
        )
        
        # Group by academy for better readability
        academy_groups = {}
        for slot in slots:
            academy = slot['academy']
            if academy not in academy_groups:
                academy_groups[academy] = []
            academy_groups[academy].append(slot)
        
        message_parts = [header]
        
        for academy_name, academy_slots in academy_groups.items():
            # Get short academy name
            short_name = academy_name.replace("Pullela Gopichand Badminton Academy", "").strip()
            if not short_name:
                short_name = academy_name.split()[0]
            
            message_parts.append(f"🏛️ {short_name} ({len(academy_slots)} slots):")
            
            for slot in academy_slots[:5]:  # Limit to 5 slots per academy in batch
                preference_emoji = "⭐" if slot.get("preference_level") == "preferred" else ""
                
                # Format date
                try:
                    date_obj = datetime.strptime(slot["date"], "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d %b")
                except:
                    formatted_date = slot["date"]
                
                message_parts.append(
                    f"  {preference_emoji} {formatted_date} • {slot['court']} • {slot['time']}"
                )
            
            if len(academy_slots) > 5:
                message_parts.append(f"  ... and {len(academy_slots) - 5} more slots")
            
            message_parts.append("")
        
        message_parts.append("🔗 Book at: https://booking.gopichandacademy.com/")
        message_parts.append("⚡ Book quickly as slots fill up fast!")
        
        return "\n".join(message_parts)
    
    async def _send_telegram_message(self, message: str) -> bool:
        """Send message via Telegram Bot API"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            
            payload = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logging.info("Telegram message sent successfully")
                return True
            else:
                logging.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"Error sending Telegram message: {str(e)}")
            return False
    
    async def send_error_notification(self, error_message: str):
        """Send error notification to user"""
        message = (
            f"❌ BADMINTON CHECKER ERROR\n\n"
            f"The badminton slot checker encountered an error:\n\n"
            f"🔍 Error: {error_message}\n\n"
            f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"The system will retry on the next scheduled run."
        )
        
        await self._send_telegram_message(message)
    
    async def send_summary_notification(self, summary: Dict[str, Any]):
        """Send summary of checking session"""
        stats = summary.get("stats", {})
        total_slots = stats.get("total_slots", 0)
        academies_with_slots = stats.get("academies_with_slots", [])
        
        if total_slots == 0:
            message = (
                f"🔍 BADMINTON CHECK COMPLETE\n\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"📊 No available slots found\n"
                f"🏢 Checked all academies\n\n"
                f"Will check again in 15 minutes..."
            )
        else:
            message = (
                f"📊 BADMINTON CHECK SUMMARY\n\n"
                f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"🏸 Total slots found: {total_slots}\n"
                f"🏢 Academies with slots: {len(academies_with_slots)}\n"
            )
            
            if academies_with_slots:
                message += f"📍 {', '.join(academies_with_slots)}\n"
            
            message += "\nNext check in 15 minutes..."
        
        await self._send_telegram_message(message)
    
    def send_email_notification(self, slots: List[Dict[str, Any]]) -> bool:
        """Send email notification (fallback method)"""
        if not self.email_config:
            return False
        
        try:
            smtp_server = self.email_config.get("smtp_server")
            smtp_port = self.email_config.get("smtp_port", 587)
            username = self.email_config.get("username")
            password = self.email_config.get("password")
            
            if not all([smtp_server, username, password]):
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = username
            msg['To'] = username  # Send to self
            msg['Subject'] = f"Badminton Slots Available - {len(slots)} slots found"
            
            # Email body
            body = "Available Badminton Slots:\n\n"
            for slot in slots:
                body += f"Academy: {slot['academy']}\n"
                body += f"Date: {slot['date']}\n"
                body += f"Court: {slot['court']}\n"
                body += f"Time: {slot['time']}\n"
                body += f"URL: {slot['booking_url']}\n\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
            server.quit()
            
            logging.info("Email notification sent successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error sending email notification: {str(e)}")
            return False
    
    async def send_startup_notification(self):
        """Send notification when the checker starts"""
        message = (
            f"🚀 BADMINTON CHECKER STARTED\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"🔍 Now monitoring for available slots\n"
            f"📱 You will be notified when slots become available\n\n"
            f"🏸 Happy playing!"
        )
        
        await self._send_telegram_message(message)
    
    def cleanup_old_notifications(self, days_to_keep: int = 7):
        """Clean up old notification records"""
        try:
            cutoff_date = datetime.now() - datetime.timedelta(days=days_to_keep)
            
            cleaned_notifications = {}
            for slot_key, timestamp_str in self.sent_notifications.items():
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    if timestamp > cutoff_date:
                        cleaned_notifications[slot_key] = timestamp_str
                except:
                    continue
            
            self.sent_notifications = cleaned_notifications
            self._save_sent_notifications()
            
            logging.info(f"Cleaned up old notification records, kept {len(cleaned_notifications)} recent ones")
            
        except Exception as e:
            logging.error(f"Error cleaning up notifications: {str(e)}")
    
    async def test_notification_system(self) -> bool:
        """Test the notification system"""
        test_message = (
            f"🧪 BADMINTON CHECKER TEST\n\n"
            f"This is a test notification to verify the system is working.\n\n"
            f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"If you received this, notifications are working correctly! 🎉"
        )
        
        success = await self._send_telegram_message(test_message)
        
        if success:
            logging.info("Test notification sent successfully")
        else:
            logging.error("Test notification failed")
        
        return success
