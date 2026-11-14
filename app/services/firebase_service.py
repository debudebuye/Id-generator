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
                if not service_account_path:
                    # Default path if not set
                    service_account_path = 'firebase-service-account.json'
                
                # Make path relative to telegram_bot directory
                if not os.path.isabs(service_account_path):
                    service_account_path = os.path.join(os.path.dirname(__file__), '..', '..', 'telegram_bot', service_account_path)
                
                storage_bucket = os.getenv('FIREBASE_STORAGE_BUCKET')
                options = {'storageBucket': storage_bucket} if storage_bucket else {}

                if os.path.exists(service_account_path):
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred, options)
                    print("✅ Firebase initialized with service account key")
                elif os.getenv('GOOGLE_CLOUD_PROJECT') or os.getenv('K_SERVICE'):
                    # No key file baked into the image - use the identity Cloud Run
                    # attaches to the container (Application Default Credentials)
                    # instead of shipping a long-lived key as a secret.
                    # K_SERVICE is set by Cloud Run on every revision.
                    firebase_admin.initialize_app(credentials.ApplicationDefault(), options)
                    print("✅ Firebase initialized with Application Default Credentials (Cloud Run)")
                else:
                    print(f"⚠️ Firebase service account file not found: {service_account_path}")
                    print("Using local storage fallback")
                    self.db = None
                    return
            
            self.db = firestore.client()
            print("✅ Firebase Firestore client initialized")
            
        except Exception as e:
            print(f"⚠️ Firebase initialization failed: {e}")
            print("Using local storage fallback")
            self.db = None
        
        self.collection_name = 'approved_users'
        self.users_collection = 'users'  # New collection for all user data
    
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

    def create_or_update_user(self, user_data: Dict) -> bool:
        """Create or update user data in Firebase"""
        try:
            if not self.db:
                return self._fallback_create_or_update_user(user_data)
            
            # Use telegramId as document ID
            doc_id = str(user_data.get('telegramId', user_data.get('id')))
            
            # Add timestamps
            current_time = datetime.utcnow().isoformat() + "Z"
            
            # Get existing user data if it exists
            doc_ref = self.db.collection(self.users_collection).document(doc_id)
            existing_doc = doc_ref.get()
            
            if existing_doc.exists:
                # Update existing user
                existing_data = existing_doc.to_dict()
                user_data['created_at'] = existing_data.get('created_at', current_time)
                user_data['updated_at'] = current_time
                doc_ref.update(user_data)
                print(f"✅ Updated user {doc_id} in Firebase")
            else:
                # Create new user
                user_data['created_at'] = current_time
                user_data['updated_at'] = current_time
                doc_ref.set(user_data)
                print(f"✅ Created user {doc_id} in Firebase")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating/updating user in Firebase: {e}")
            return self._fallback_create_or_update_user(user_data)
    
    def get_user_data(self, telegram_id: str) -> Optional[Dict]:
        """Get user data from Firebase"""
        try:
            if not self.db:
                return self._fallback_get_user_data(telegram_id)
            
            doc_ref = self.db.collection(self.users_collection).document(str(telegram_id))
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                return user_data
            
            return None
            
        except Exception as e:
            print(f"❌ Error getting user data from Firebase: {e}")
            return self._fallback_get_user_data(telegram_id)
    
    def update_user_preferences(self, telegram_id: str, preferences: Dict) -> bool:
        """Update user preferences in Firebase"""
        try:
            if not self.db:
                return self._fallback_update_user_preferences(telegram_id, preferences)
            
            doc_ref = self.db.collection(self.users_collection).document(str(telegram_id))
            
            # Update preferences and timestamp
            update_data = {
                'preferences': preferences,
                'updated_at': datetime.utcnow().isoformat() + "Z"
            }
            
            doc_ref.update(update_data)
            print(f"✅ Updated preferences for user {telegram_id} in Firebase")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user preferences in Firebase: {e}")
            return self._fallback_update_user_preferences(telegram_id, preferences)
    
    def update_user_access_status(self, telegram_id: str, status: str) -> bool:
        """Update user access status in Firebase"""
        try:
            if not self.db:
                return self._fallback_update_user_access_status(telegram_id, status)
            
            doc_ref = self.db.collection(self.users_collection).document(str(telegram_id))
            
            # Update status and timestamp
            update_data = {
                'access_status': status,
                'updated_at': datetime.utcnow().isoformat() + "Z"
            }
            
            if status == 'approved':
                update_data['approved_at'] = datetime.utcnow().isoformat() + "Z"
            elif status == 'rejected':
                update_data['rejected_at'] = datetime.utcnow().isoformat() + "Z"
            elif status == 'paused':
                update_data['paused_at'] = datetime.utcnow().isoformat() + "Z"
            
            doc_ref.update(update_data)
            print(f"✅ Updated access status for user {telegram_id} to {status} in Firebase")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user access status in Firebase: {e}")
            return self._fallback_update_user_access_status(telegram_id, status)
    
    def get_all_users_detailed(self) -> List[Dict]:
        """Get all users with detailed information"""
        try:
            if not self.db:
                return self._fallback_get_all_users_detailed()
            
            users = []
            docs = self.db.collection(self.users_collection).stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                users.append(user_data)
            
            # Sort by creation date (newest first)
            users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            return users
            
        except Exception as e:
            print(f"❌ Error getting detailed users from Firebase: {e}")
            return self._fallback_get_all_users_detailed()
    
    def get_rejected_users(self) -> List[Dict]:
        """Get all rejected users"""
        try:
            if not self.db:
                return self._fallback_get_rejected_users()
            
            users = []
            docs = self.db.collection(self.users_collection).where('access_status', '==', 'rejected').stream()
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['id'] = doc.id
                users.append(user_data)
            
            # Sort by rejection date (newest first)
            users.sort(key=lambda x: x.get('rejected_at', ''), reverse=True)
            return users
            
        except Exception as e:
            print(f"❌ Error getting rejected users from Firebase: {e}")
            return self._fallback_get_rejected_users()
    
    # Fallback methods for local storage
    def _fallback_create_or_update_user(self, user_data: Dict) -> bool:
        """Fallback to local JSON storage for user data"""
        try:
            file_path = 'telegram_bot/data/users.json'
            users = []
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            
            # Find existing user
            telegram_id = str(user_data.get('telegramId', user_data.get('id')))
            existing_user_index = None
            
            for i, user in enumerate(users):
                if str(user.get('telegramId', user.get('id'))) == telegram_id:
                    existing_user_index = i
                    break
            
            # Add timestamps
            current_time = datetime.utcnow().isoformat() + "Z"
            
            if existing_user_index is not None:
                # Update existing user
                user_data['created_at'] = users[existing_user_index].get('created_at', current_time)
                user_data['updated_at'] = current_time
                users[existing_user_index] = user_data
                print(f"✅ Updated user {telegram_id} in local storage")
            else:
                # Create new user
                user_data['created_at'] = current_time
                user_data['updated_at'] = current_time
                users.append(user_data)
                print(f"✅ Created user {telegram_id} in local storage")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating/updating user in local storage: {e}")
            return False
    
    def _fallback_get_user_data(self, telegram_id: str) -> Optional[Dict]:
        """Fallback to local JSON storage for getting user data"""
        try:
            file_path = 'telegram_bot/data/users.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                for user in users:
                    if str(user.get('telegramId', user.get('id'))) == str(telegram_id):
                        return user
            
            return None
        except Exception as e:
            print(f"❌ Error getting user data from local storage: {e}")
            return None
    
    def _fallback_update_user_preferences(self, telegram_id: str, preferences: Dict) -> bool:
        """Fallback to local JSON storage for updating preferences"""
        try:
            file_path = 'telegram_bot/data/users.json'
            users = []
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            
            # Find and update user
            for user in users:
                if str(user.get('telegramId', user.get('id'))) == str(telegram_id):
                    user['preferences'] = preferences
                    user['updated_at'] = datetime.utcnow().isoformat() + "Z"
                    break
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Updated preferences for user {telegram_id} in local storage")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user preferences in local storage: {e}")
            return False
    
    def _fallback_update_user_access_status(self, telegram_id: str, status: str) -> bool:
        """Fallback to local JSON storage for updating access status"""
        try:
            file_path = 'telegram_bot/data/users.json'
            users = []
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            
            # Find and update user
            current_time = datetime.utcnow().isoformat() + "Z"
            for user in users:
                if str(user.get('telegramId', user.get('id'))) == str(telegram_id):
                    user['access_status'] = status
                    user['updated_at'] = current_time
                    
                    if status == 'approved':
                        user['approved_at'] = current_time
                    elif status == 'rejected':
                        user['rejected_at'] = current_time
                    elif status == 'paused':
                        user['paused_at'] = current_time
                    break
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Updated access status for user {telegram_id} to {status} in local storage")
            return True
            
        except Exception as e:
            print(f"❌ Error updating user access status in local storage: {e}")
            return False
    
    def _fallback_get_all_users_detailed(self) -> List[Dict]:
        """Fallback to local JSON storage for getting all users"""
        try:
            file_path = 'telegram_bot/data/users.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                # Sort by creation date (newest first)
                users.sort(key=lambda x: x.get('created_at', ''), reverse=True)
                return users
            return []
        except Exception as e:
            print(f"❌ Error reading detailed users from local storage: {e}")
            return []
    
    def _fallback_get_rejected_users(self) -> List[Dict]:
        """Fallback to local JSON storage for getting rejected users"""
        try:
            file_path = 'telegram_bot/data/users.json'
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    users = json.load(f)
                
                # Filter rejected users
                rejected_users = [user for user in users if user.get('access_status') == 'rejected']
                # Sort by rejection date (newest first)
                rejected_users.sort(key=lambda x: x.get('rejected_at', ''), reverse=True)
                return rejected_users
            return []
        except Exception as e:
            print(f"❌ Error reading rejected users from local storage: {e}")
            return []

# Global instance
firebase_service = FirebaseService()
