# Jaikalki HRMS — Mobile (Flutter)

Multi-platform Flutter client for **Jaikalki Technology Pvt Ltd** — runs on
Android, iOS, and Web from a single codebase.

## Quick start

```bash
flutter pub get

# Mobile
flutter run

# Web (Chrome)
flutter run -d chrome

# Builds
flutter build apk        # Android
flutter build web        # Web
# flutter build ios      # iOS (Mac only)
```

API base URL is read from the `API_BASE_URL` Dart-define and defaults to
`http://localhost:8000`. Override at build time:

```bash
flutter run --dart-define=API_BASE_URL=https://api.jaikalki.com
```

## Stack

- Flutter 3.22+, Dart 3.4+
- `flutter_bloc` + `equatable` for state
- `go_router` for navigation
- `get_it` for DI
- `dio` for HTTP, `flutter_secure_storage` for tokens
- `google_fonts` (Playfair Display, Poppins, JetBrains Mono)

## Project layout

```
lib/
  main.dart, app.dart
  core/
    constants/   AppConstants (company, API URL)
    theme/       AppColors, AppTheme (light + dark)
    network/     DioClient, AuthInterceptor, LoggingInterceptor
    storage/     SecureStorage wrapper
    routing/     go_router routes
    di/          GetIt setup
  features/
    splash/, auth/, dashboard/   (Phase 0 skeletons)
  shared/
    widgets/, extensions/
assets/
  branding/   Jaikalki logos / splash / icons
  images/, icons/
```

## Brand tokens

Color values in `lib/core/theme/app_colors.dart` mirror the React admin's
Tailwind config and the design-system HTML at
`/app_designed/jaikalki-design.html`.

## Phase status

- Phase 0 ✅ — Foundation: theme, routing, DI, dio + secure storage,
  splash + login + dashboard skeletons.
- Phase 1 — Auth: real login flow against `/api/v1/auth/login`,
  refresh-token rotation, biometric unlock.
- Phase 2 — Employee profile, document uploads.
