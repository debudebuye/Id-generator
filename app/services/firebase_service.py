#!/usr/bin/env python3
"""
Firebase service for managing approved users
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

class FirebaseService:
    def __init__(self):
        """Initialize Firebase connection"""
        # Load environment variables
        load_dotenv('telegram_bot/.env')
        
        # Try to initialize Firebase
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Try to use service account key if available
                service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
                if service_account_path:
                    # Make path relative to telegram_bot directory
                    if not os.path.isabs(service_account_path):
                        service_account_path = os.path.join(os.path.dirname(__file__), '..', '..', 'telegram_bot', service_account_path)
                    
                    if os.path.exists(service_account_path):
                        cred = credentials.Certificate(service_account_path)
                        firebase_admin.initialize_app(cred)
                        print("✅ Firebase initialized with service account key")
                    else:
                        print(f"⚠️ Firebase service account file not found: {service_account_path}")
                        print("Using local storage fallback")
                        self.db = None
                        return
                else:
                    print("ℹ️ FIREBASE_SERVICE_ACCOUNT_PATH not set, using local storage")
                    self.db = None
                    return
            
            self.db = firestore.client()
            print("✅ Firebase Firestore client initialized")
            
        except Exception as e:
            print(f"⚠️ Firebase initialization failed: {e}")
            print("Using local storage fallback")
            self.db = None
        
        self.collection_name = 'approved_users'
    
    def add_approved_user(self, user_data: Dict) -> bool:
        """Add a user to the approved users collection"""
        try:
            if not self.db:
                return self._fallback_add_user(user_data)
            
            # Add timestamp
            user_data['approved_at'] = datetime.utcnow().isoformat() + "Z"
            user_data['status'] = 'approved'
            
            # Use telegramId as document ID for uniqueness
            doc_id = str(user_data.get('telegramId', user_data.get('id')))
            
            # Check if user already exists
            doc_ref = self.db.collection(self.collection_name).document(doc_id)
            if doc_ref.get().exists:
                print(f"ℹ️ User {doc_id} already exists in approved users")
                return True
            
            # Add user to Firestore
            doc_ref.set(user_data)
            print(f"✅ Added user {doc_id} ({user_data.get('firstName', 'Unknown')}) to Firebase")
            return True
            
        except Exception as e:
            print(f"❌ Error adding user to Firebase: {e}")
            return self._fallback_add_user(user_data)
    
    def get_approved_users(self) -> List[Dict]:
        """Get all approved users"""
        try:
            if not self.db:
                return self._fallback_get_users()
            
            users = []
            docs = self.db.collection(self.collection_name).stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                users.append(user_data)
            
            # Sort by approval date (newest first)
            users.sort(key=lambda x: x.get('approved_at', ''), reverse=True)
            return users
            
        except Exception as e:
            print(f"❌ Error getting users from Firebase: {e}")
            return self._fallback_get_users()
    
    def remove_approved_user(self, telegram_id: str) -> bool:
        """Remove a user from approved users"""
        try:
            if not self.db:
                return self._fallback_remove_user(telegram_id)
            
            doc_ref = self.db.collection(self.collection_name).document(str(telegram_id))
            if doc_ref.get().exists:
                doc_ref.delete()
                print(f"✅ Removed user {telegram_id} from Firebase")
                return True
            else:
                print(f"ℹ️ User {telegram_id} not found in Firebase")
                return False
                
        except Exception as e:
            print(f"❌ Error removing user from Firebase: {e}")
            return self._fallback_remove_user(telegram_id)
    
    def _fallback_add_user(self, user_data: Dict) -> bool:
        """Fallback to local JSON storage"""
        try:
            file_path = 'telegram_bot/data/approved_users.json'
            users = []
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            
            # Add timestamp
            user_data['approved_at'] = datetime.utcnow().isoformat() + "Z"
            user_data['status'] = 'approved'
            
            # Check if user already exists
            telegram_id = str(user_data.get('telegramId', user_data.get('id')))
            if any(str(user.get('telegramId', user.get('id'))) == telegram_id for user in users):
                print(f"ℹ️ User {telegram_id} already exists in local storage")
                return True
            
            users.append(user_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Added user {telegram_id} ({user_data.get('firstName', 'Unknown')}) to local storage")
            return True
            
        except Exception as e:
            print(f"❌ Error adding user to local storage: {e}")
            return False
    
    def _fallback_get_users(self) -> List[Dict]:
        """Fallback to local JSON storage"""
        try:
            file_path = 'telegram_bot/data/approved_users.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                # Sort by approval date (newest first)
                users.sort(key=lambda x: x.get('approved_at', ''), reverse=True)
                return users
            return []
        except Exception as e:
            print(f"❌ Error reading from local storage: {e}")
            return []
    
    def _fallback_remove_user(self, telegram_id: str) -> bool:
        """Fallback to local JSON storage"""
        try:
            file_path = 'telegram_bot/data/approved_users.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                # Remove user
                original_count = len(users)
                users = [user for user in users if str(user.get('telegramId', user.get('id'))) != str(telegram_id)]
                
                if len(users) < original_count:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(users, f, ensure_ascii=False, indent=2)
                    print(f"✅ Removed user {telegram_id} from local storage")
                    return True
                else:
                    print(f"ℹ️ User {telegram_id} not found in local storage")
                    return False
            return False
        except Exception as e:
            print(f"❌ Error removing user from local storage: {e}")
            return False

# Global instance
firebase_service = FirebaseService()
