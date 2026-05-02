# Firebase Cloud Messaging (FCM) — End-to-End Setup

This document covers wiring real push notifications for Jaikalki HRMS:
backend (FastAPI), Android (Flutter), and iOS (Flutter). The backend
falls back gracefully when FCM is not configured (rows are stored as
`pending`), so dev environments don't need Firebase to run.

---

## 1. Firebase Console — one-time

1. Open <https://console.firebase.google.com/> and create (or open) the
   project. The current project is **`hrms-jailakali`**.
2. **Add Android app** with package name `com.hrms.jaikalki`. Download
   the generated `google-services.json` and drop it into
   `hrms_mobile/android/app/google-services.json`.
3. **Add iOS app** with bundle id matching `Runner.xcodeproj` (default:
   `com.hrms.jaikalki`). Download `GoogleService-Info.plist` and drop
   it into `hrms_mobile/ios/Runner/GoogleService-Info.plist` (open the
   Xcode workspace and add it to the Runner target).
4. **APNs Authentication Key** (iOS only): Apple Developer → Keys →
   create a key with "Apple Push Notifications service (APNs)" enabled.
   Download the `.p8`. In Firebase Console → Project Settings → Cloud
   Messaging → iOS app, upload the `.p8` and fill Key ID + Team ID.
   Without this, iOS pushes never leave Firebase.
5. **Service-account JSON** (backend): Project Settings → Service
   accounts → "Generate new private key". Save the JSON somewhere safe
   — it grants full push-send privileges.

---

## 2. Backend (FastAPI / gunicorn)

### 2.1 Place the service-account JSON

Pick whichever style you prefer:

- **Auto-discovery (dev-friendly)**: drop the JSON anywhere inside
  `hrms_backend/app/credential/`. The service auto-picks the first
  file matching `*firebase*adminsdk*.json` (or any `*.json` if no
  match). The directory is tracked in git but `*.json` files are
  gitignored.
- **Explicit path (recommended for prod)**: set
  `FCM_CREDENTIALS_PATH=/etc/jaikalki/firebase-service-account.json`
  in your `.env`. The file must be readable by the gunicorn user.

### 2.2 .env entries

```env
# ── Firebase Cloud Messaging ──────────────────────────────────
FCM_PROJECT_ID=hrms-jailakali
FCM_CREDENTIALS_PATH=/etc/jaikalki/firebase-service-account.json
```

`FCM_PROJECT_ID` is optional; the SDK reads it from the JSON when
omitted, but setting it explicitly catches credential/JSON mismatches.

### 2.3 Production deployment (gunicorn)

The current production command is:

```bash
gunicorn app.main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:3690 \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --access-logfile - \
  --error-logfile -
```

Steps to deploy:

1. `scp` the service-account JSON to the host:
   `/etc/jaikalki/firebase-service-account.json`
2. Lock it down: `sudo chown <gunicorn-user>:<gunicorn-user>
   /etc/jaikalki/firebase-service-account.json && sudo chmod 600 …`
3. Update `/etc/jaikalki/.env` (or wherever you keep prod env) with
   the two `FCM_*` keys above.
4. Restart gunicorn (systemd `systemctl restart jaikalki-hrms` or
   whatever your unit is named).
5. Verify with `curl http://127.0.0.1:3690/api/v1/health/ready` —
   the `fcm` block should report `configured: true` and
   `initialised: true`.

### 2.4 Verify

```bash
curl -s http://127.0.0.1:3690/api/v1/health/ready | jq .checks.fcm
```

Expected when configured:

```json
{
  "configured": true,
  "credentials_path": "/etc/jaikalki/firebase-service-account.json",
  "project_id": "hrms-jailakali",
  "initialised": true,
  "status": "ok"
}
```

When unconfigured the service still boots — `configured` is `false`
and notifications are written to the DB with `status='pending'`.

---

## 3. Android (Flutter)

The repo already contains all the Gradle wiring. To verify:

- `hrms_mobile/android/settings.gradle.kts` declares
  `id("com.google.gms.google-services") version "4.4.2" apply false`.
- `hrms_mobile/android/app/build.gradle.kts` applies
  `id("com.google.gms.google-services")` and sets:
  - `namespace = "com.hrms.jaikalki"`
  - `applicationId = "com.hrms.jaikalki"` (must match the
    `package_name` in `google-services.json`)
  - `minSdk = 21` (firebase_messaging requires ≥ 19; 21 is the Flutter
    default).
  - `multiDexEnabled = true`
- `AndroidManifest.xml` declares `POST_NOTIFICATIONS` (Android 13+).
- The launcher activity (`MainActivity.kt`) lives at
  `android/app/src/main/kotlin/com/hrms/jaikalki/MainActivity.kt`.

After downloading `google-services.json` from the console:

```bash
cd hrms_mobile
flutter clean
flutter pub get
flutter run
```

If you see "no matching client found for package name" at gradle-sync
time, the `package_name` inside `google-services.json` doesn't match
`applicationId`. Re-add the Android app in Firebase with
`com.hrms.jaikalki` and re-download.

---

## 4. iOS (Flutter)

1. Drop `GoogleService-Info.plist` into `hrms_mobile/ios/Runner/` and
   add it to the Runner target in Xcode.
2. `Info.plist` already declares:
   - `UIBackgroundModes = [fetch, remote-notification]`
   - `FirebaseAppDelegateProxyEnabled = true`
3. `AppDelegate.swift` already calls
   `application.registerForRemoteNotifications()` in
   `didFinishLaunchingWithOptions`.
4. In Xcode → Runner target → Signing & Capabilities, add the
   **Push Notifications** capability.
5. Bump the iOS deployment target to ≥ 13.0 (firebase_core requires
   it). Check `ios/Podfile` after the first `pod install`:
   `platform :ios, '13.0'`.
6. Build:

   ```bash
   cd hrms_mobile/ios
   pod install
   cd ..
   flutter run -d <ios-device>
   ```

7. Ensure the **APNs Authentication Key** is uploaded in Firebase
   Console (see §1.4). Without it, iOS devices register but Firebase
   can't deliver.

---

## 5. Mobile lifecycle reference

Implemented in `hrms_mobile/lib/core/push/push_notifications_service.dart`:

- `PushNotificationsService.instance.initialize()` — called from
  `main.dart` before `runApp()`. Boots Firebase, requests permission,
  creates the local-notifications channel, registers the three
  message handlers (foreground / background / terminated).
- `PushNotificationsService.instance.registerToken(api)` — called
  from `AuthBloc` after a successful login / token-refresh / cold
  start with a valid session. Sends `POST /notifications/devices`.
- `PushNotificationsService.instance.unregisterToken(api)` — called
  on logout. Best-effort: deletes the FCM token locally and clears
  the cached copy.

The Android channel id is `jaikalki_default` (high importance). The
foreground display path goes through `flutter_local_notifications`
because FCM only auto-banners background/terminated apps.

---

## 6. Smoke test

```bash
# 1. Login on a device, check the backend log for
#    "POST /api/v1/notifications/devices 204"

# 2. Trigger a server-side notification (e.g. mark an attendance
#    request approved). The corresponding device row must have
#    status='delivered' instead of 'pending'.

# 3. Inspect:
mysql -u root -p db_hrms_jaikalki \
  -e "SELECT id, user_id, channel, status, error \
      FROM notification_deliveries ORDER BY id DESC LIMIT 10;"
```

If you see `status='failed'`, the `error` column contains the FCM
error code — `UNREGISTERED` means the token expired (the user
reinstalled the app), `INVALID_ARGUMENT` usually means project-id
mismatch, `SENDER_ID_MISMATCH` means the
`google-services.json` / `GoogleService-Info.plist` doesn't match
the service-account project.

---

## 7. Rotating credentials

If a service-account JSON is ever committed by accident:

1. Firebase Console → Project Settings → Service accounts → revoke
   the leaked key.
2. Generate a new one, scp to the host, restart gunicorn.
3. Force-purge the file from git history with `git filter-repo` or
   BFG if the leaked commit is still on remote.

This repo had the JSON committed once at initial setup; that key
should be considered compromised and rotated before any production
push traffic flows through it.
