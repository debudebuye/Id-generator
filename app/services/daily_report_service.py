import json
import os
from datetime import datetime, timezone
import pytz
from typing import Dict, List, Optional

class DailyReportService:
    """Service to track ID generation counts and daily reports."""
    
    def __init__(self, data_folder: str = "telegram_bot/data"):
        self.data_folder = data_folder
        self.ethiopia_tz = pytz.timezone('Africa/Addis_Ababa')
        self.daily_reports_file = os.path.join(data_folder, "daily_reports.json")
        self.user_stats_file = os.path.join(data_folder, "user_stats.json")
        self.user_status_file = os.path.join(data_folder, "user_status.json")
        self.bot_status_file = os.path.join(data_folder, "bot_status.json")
        self._ensure_data_files()
    
    def _ensure_data_files(self):
        """Ensure data files exist."""
        os.makedirs(self.data_folder, exist_ok=True)
        
        if not os.path.exists(self.daily_reports_file):
            with open(self.daily_reports_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        if not os.path.exists(self.user_stats_file):
            with open(self.user_stats_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        if not os.path.exists(self.user_status_file):
            with open(self.user_status_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
        
        if not os.path.exists(self.bot_status_file):
            with open(self.bot_status_file, 'w', encoding='utf-8') as f:
                json.dump({"paused": False, "paused_by": None, "paused_at": None}, f, ensure_ascii=False, indent=2)
    
    def _get_ethiopia_time(self) -> datetime:
        """Get current time in Ethiopia timezone."""
        return datetime.now(self.ethiopia_tz)
    
    def _get_today_key(self) -> str:
        """Get today's date key in Ethiopia timezone."""
        return self._get_ethiopia_time().strftime("%Y-%m-%d")
    
    def increment_id_count(self, user_id: int, username: str = None) -> Dict:
        """Increment ID generation count for a user today."""
        try:
            # Load current user stats
            with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            
            today_key = self._get_today_key()
            user_key = str(user_id)
            
            # Initialize user data if not exists
            if user_key not in user_stats:
                user_stats[user_key] = {
                    "username": username or f"user_{user_id}",
                    "total_generated": 0,
                    "total_paid": 0,
                    "total_unpaid": 0,
                    "daily_counts": {},
                    "daily_payment_status": {}
                }
            
            # Update username if provided
            if username:
                user_stats[user_key]["username"] = username
            
            # Initialize today's count if not exists
            if today_key not in user_stats[user_key]["daily_counts"]:
                user_stats[user_key]["daily_counts"][today_key] = 0
                user_stats[user_key]["daily_payment_status"][today_key] = {
                    "paid": 0,
                    "unpaid": 0
                }
            
            # Increment counts
            user_stats[user_key]["daily_counts"][today_key] += 1
            user_stats[user_key]["total_generated"] += 1
            user_stats[user_key]["daily_payment_status"][today_key]["unpaid"] += 1
            user_stats[user_key]["total_unpaid"] += 1
            
            # Save updated stats
            with open(self.user_stats_file, 'w', encoding='utf-8') as f:
                json.dump(user_stats, f, ensure_ascii=False, indent=2)
            
            # Get current counts for return
            today_count = user_stats[user_key]["daily_counts"][today_key]
            total_count = user_stats[user_key]["total_generated"]
            today_unpaid = user_stats[user_key]["daily_payment_status"][today_key]["unpaid"]
            total_unpaid = user_stats[user_key]["total_unpaid"]
            
            return {
                "today_count": today_count,
                "total_count": total_count,
                "today_unpaid": today_unpaid,
                "total_unpaid": total_unpaid,
                "date": today_key,
                "username": user_stats[user_key]["username"]
            }
            
        except Exception as e:
            print(f"Error incrementing ID count: {str(e)}")
            return {
                "today_count": 1,
                "total_count": 1,
                "today_unpaid": 1,
                "total_unpaid": 1,
                "date": self._get_today_key(),
                "username": username or f"user_{user_id}"
            }
    
    def get_user_today_count(self, user_id: int) -> int:
        """Get today's ID generation count for a user."""
        try:
            with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            
            user_key = str(user_id)
            today_key = self._get_today_key()
            
            if user_key in user_stats and today_key in user_stats[user_key]["daily_counts"]:
                return user_stats[user_key]["daily_counts"][today_key]
            
            return 0
            
        except Exception as e:
            print(f"Error getting user today count: {str(e)}")
            return 0
    
    def get_user_stats(self, user_id: int) -> Dict:
        """Get complete stats for a user."""
        try:
            with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            
            user_key = str(user_id)
            today_key = self._get_today_key()
            
            if user_key in user_stats:
                stats = user_stats[user_key].copy()
                stats["today_count"] = stats["daily_counts"].get(today_key, 0)
                stats["today_paid"] = stats["daily_payment_status"].get(today_key, {}).get("paid", 0)
                stats["today_unpaid"] = stats["daily_payment_status"].get(today_key, {}).get("unpaid", 0)
                stats["total_paid"] = stats.get("total_paid", 0)
                stats["total_unpaid"] = stats.get("total_unpaid", 0)
                return stats
            
            return {
                "username": f"user_{user_id}",
                "total_generated": 0,
                "total_paid": 0,
                "total_unpaid": 0,
                "daily_counts": {},
                "daily_payment_status": {},
                "today_count": 0,
                "today_paid": 0,
                "today_unpaid": 0
            }
            
        except Exception as e:
            print(f"Error getting user stats: {str(e)}")
            return {
                "username": f"user_{user_id}",
                "total_generated": 0,
                "total_paid": 0,
                "total_unpaid": 0,
                "daily_counts": {},
                "daily_payment_status": {},
                "today_count": 0,
                "today_paid": 0,
                "today_unpaid": 0
            }
    
    def generate_daily_report(self, date: str = None) -> Dict:
        """Generate daily report for a specific date (default: today)."""
        try:
            if date is None:
                date = self._get_today_key()
            
            with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            
            report = {
                "date": date,
                "total_users": 0,
                "total_generated": 0,
                "users": []
            }
            
            for user_id, stats in user_stats.items():
                if date in stats.get("daily_counts", {}):
                    count = stats["daily_counts"][date]
                    if count > 0:
                        # Handle missing payment status fields gracefully
                        payment_status = stats.get("daily_payment_status", {}).get(date, {"paid": 0, "unpaid": count})
                        # If no payment status exists, assume all are unpaid
                        if "daily_payment_status" not in stats:
                            payment_status = {"paid": 0, "unpaid": count}
                        
                        report["users"].append({
                            "user_id": int(user_id),
                            "username": stats.get("username", f"user_{user_id}"),
                            "count": count,
                            "paid": payment_status.get("paid", 0),
                            "unpaid": payment_status.get("unpaid", count),
                            "payment_due": payment_status.get("unpaid", count) * 50  # 50 birr per unpaid ID
                        })
                        report["total_generated"] += count
                        report["total_users"] += 1
            
            # Sort users by count (descending)
            report["users"].sort(key=lambda x: x["count"], reverse=True)
            
            # Save daily report
            with open(self.daily_reports_file, 'r', encoding='utf-8') as f:
                daily_reports = json.load(f)
            
            daily_reports[date] = report
            
            with open(self.daily_reports_file, 'w', encoding='utf-8') as f:
                json.dump(daily_reports, f, ensure_ascii=False, indent=2)
            
            return report
            
        except Exception as e:
            print(f"Error generating daily report: {str(e)}")
            return {
                "date": date or self._get_today_key(),
                "total_users": 0,
                "total_generated": 0,
                "users": []
            }
    
    def get_daily_report(self, date: str = None) -> Dict:
        """Get daily report for a specific date."""
        try:
            if date is None:
                date = self._get_today_key()
            
            with open(self.daily_reports_file, 'r', encoding='utf-8') as f:
                daily_reports = json.load(f)
            
            if date in daily_reports:
                return daily_reports[date]
            
            # Generate report if not exists
            return self.generate_daily_report(date)
            
        except Exception as e:
            print(f"Error getting daily report: {str(e)}")
            return self.generate_daily_report(date)
    
    def get_all_daily_reports(self) -> Dict:
        """Get all daily reports."""
        try:
            with open(self.daily_reports_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error getting all daily reports: {str(e)}")
            return {}
    
    def is_bot_pause_time(self) -> bool:
        """Check if it's time to pause the bot (5 PM Ethiopia time)."""
        ethiopia_time = self._get_ethiopia_time()
        return ethiopia_time.hour >= 17  # 5 PM
    
    def get_pause_message(self) -> str:
        """Get the pause message for users."""
        ethiopia_time = self._get_ethiopia_time()
        return f"🕔 Bot is currently paused for daily maintenance.\n\n⏰ Current time: {ethiopia_time.strftime('%H:%M')} (Ethiopia time)\n\n📊 Daily reports are being generated. The bot will resume shortly.\n\nFor support, contact @fayda_software"
    
    def get_daily_report_message(self, user_id: int) -> str:
        """Get personalized daily report message for a user."""
        try:
            stats = self.get_user_stats(user_id)
            today_count = stats["today_count"]
            total_count = stats["total_generated"]
            
            if today_count == 0:
                return f"📊 **Your Stats:**\n✅ IDs Generated Today: 0\n📈 Total Unpaid Generated: {total_count}"
            
            return f"📊 **Your Stats:**\n✅ IDs Generated Today: {today_count}\n📈 Total Unpaid Generated: {total_count}\n\n💳 Please complete your payment and attach the screenshot for admin @fayda_software"
            
        except Exception as e:
            print(f"Error generating daily report message: {str(e)}")
            return f"📊 **Your Stats:**\nError generating report. Please contact @fayda_software for support."
    
    def get_user_status(self, user_id: int) -> Dict:
        """Get user status (active/paused)."""
        try:
            with open(self.user_status_file, 'r', encoding='utf-8') as f:
                user_status = json.load(f)
            
            user_key = str(user_id)
            return user_status.get(user_key, {"status": "active", "paused_at": None, "paused_by": None})
            
        except Exception as e:
            print(f"Error getting user status: {str(e)}")
            return {"status": "active", "paused_at": None, "paused_by": None}
    
    def pause_user(self, user_id: int, paused_by: str = "admin") -> bool:
        """Pause a user."""
        try:
            with open(self.user_status_file, 'r', encoding='utf-8') as f:
                user_status = json.load(f)
            
            user_key = str(user_id)
            user_status[user_key] = {
                "status": "paused",
                "paused_at": self._get_ethiopia_time().isoformat(),
                "paused_by": paused_by
            }
            
            with open(self.user_status_file, 'w', encoding='utf-8') as f:
                json.dump(user_status, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error pausing user: {str(e)}")
            return False
    
    def resume_user(self, user_id: int, resumed_by: str = "admin") -> bool:
        """Resume a user."""
        try:
            with open(self.user_status_file, 'r', encoding='utf-8') as f:
                user_status = json.load(f)
            
            user_key = str(user_id)
            user_status[user_key] = {
                "status": "active",
                "resumed_at": self._get_ethiopia_time().isoformat(),
                "resumed_by": resumed_by
            }
            
            with open(self.user_status_file, 'w', encoding='utf-8') as f:
                json.dump(user_status, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error resuming user: {str(e)}")
            return False
    
    def is_user_paused(self, user_id: int) -> bool:
        """Check if a user is paused."""
        status = self.get_user_status(user_id)
        return status.get("status") == "paused"
    
    def get_all_user_statuses(self) -> Dict:
        """Get all user statuses."""
        try:
            with open(self.user_status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error getting all user statuses: {str(e)}")
            return {}
    
    def mark_payment_paid(self, user_id: int, date: str = None) -> bool:
        """Mark payment as paid for a user on a specific date (simple version)."""
        try:
            if date is None:
                date = self._get_today_key()
            
            with open(self.user_stats_file, 'r', encoding='utf-8') as f:
                user_stats = json.load(f)
            
            user_key = str(user_id)
            
            if user_key not in user_stats:
                return False
            
            # Initialize payment status if not exists
            if "daily_payment_status" not in user_stats[user_key]:
                user_stats[user_key]["daily_payment_status"] = {}
            if date not in user_stats[user_key]["daily_payment_status"]:
                user_stats[user_key]["daily_payment_status"][date] = {"paid": 0, "unpaid": 0}
            
            # Mark all unpaid as paid for this date
            unpaid_count = user_stats[user_key]["daily_payment_status"][date]["unpaid"]
            user_stats[user_key]["daily_payment_status"][date]["paid"] += unpaid_count
            user_stats[user_key]["daily_payment_status"][date]["unpaid"] = 0
            
            # Update totals
            user_stats[user_key]["total_paid"] = user_stats[user_key].get("total_paid", 0) + unpaid_count
            user_stats[user_key]["total_unpaid"] = max(0, user_stats[user_key].get("total_unpaid", 0) - unpaid_count)
            
            # Save updated stats
            with open(self.user_stats_file, 'w', encoding='utf-8') as f:
                json.dump(user_stats, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error marking payment as paid: {str(e)}")
            return False
    
    def is_bot_paused(self) -> bool:
        """Check if the bot is paused."""
        try:
            with open(self.bot_status_file, 'r', encoding='utf-8') as f:
                bot_status = json.load(f)
            return bot_status.get("paused", False)
        except Exception as e:
            print(f"Error checking bot status: {str(e)}")
            return False
    
    def pause_bot(self, paused_by: str = "admin") -> bool:
        """Pause the bot."""
        try:
            with open(self.bot_status_file, 'r', encoding='utf-8') as f:
                bot_status = json.load(f)
            
            bot_status["paused"] = True
            bot_status["paused_by"] = paused_by
            bot_status["paused_at"] = self._get_ethiopia_time().isoformat()
            
            with open(self.bot_status_file, 'w', encoding='utf-8') as f:
                json.dump(bot_status, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error pausing bot: {str(e)}")
            return False
    
    def resume_bot(self, resumed_by: str = "admin") -> bool:
        """Resume the bot."""
        try:
            with open(self.bot_status_file, 'r', encoding='utf-8') as f:
                bot_status = json.load(f)
            
            bot_status["paused"] = False
            bot_status["paused_by"] = None
            bot_status["paused_at"] = None
            bot_status["resumed_by"] = resumed_by
            bot_status["resumed_at"] = self._get_ethiopia_time().isoformat()
            
            with open(self.bot_status_file, 'w', encoding='utf-8') as f:
                json.dump(bot_status, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"Error resuming bot: {str(e)}")
            return False
    
    def get_bot_status(self) -> Dict:
        """Get bot status information."""
        try:
            with open(self.bot_status_file, 'r', encoding='utf-8') as f:
                bot_status = json.load(f)
            return bot_status
        except Exception as e:
            print(f"Error getting bot status: {str(e)}")
            return {"paused": False, "paused_by": None, "paused_at": None}
    
