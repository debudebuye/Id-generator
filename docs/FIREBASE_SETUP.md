# Firebase Setup Instructions

## 1. Get Firebase Service Account Key

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select your project: bot-admin-69886
3. Go to Project Settings (gear icon)
4. Go to "Service accounts" tab
5. Click "Generate new private key"
6. Download the JSON file
7. Save it as: `telegram_bot/firebase-service-account.json`

## 2. Update Environment Variables

Add to `telegram_bot/.env`:
```
FIREBASE_SERVICE_ACCOUNT_PATH=firebase-service-account.json
```

## 3. Enable Firestore Database

1. In Firebase Console, go to "Firestore Database"
2. Click "Create database"
3. Choose "Start in test mode" (for development)
4. Select a location (closest to you)

## 4. Update Firebase Service

The service will automatically detect the service account key and use Firebase instead of local storage.
