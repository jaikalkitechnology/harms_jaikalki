import 'package:flutter/foundation.dart';

class AppConstants {
  AppConstants._();

  static const String appName = 'Jaikalki HRMS';
  static const String companyName = 'Jaikalki Technology Pvt Ltd';
  static const String companyAddress =
      'Sh N B1/A Ground Floor, Mahavir Nagar, Deepak Hospital, '
      'Mira Road, Thane-401107 Maharashtra';
  static const String employeeCodePrefix = 'JKT';

  // Production API endpoint.
  static const String prodApiBaseUrl = 'https://api-hrms.jaikalki.com';

  // Local dev fallback.
  static const String devApiBaseUrl = 'http://localhost:8000';

  /// API base URL.
  ///
  /// Resolution order:
  ///   1. Compile-time `--dart-define=API_BASE_URL=...` (any build)
  ///   2. Production URL when running a release build
  ///   3. Local dev URL otherwise
  static String get apiBaseUrl {
    const override = String.fromEnvironment('API_BASE_URL');
    if (override.isNotEmpty) return override;
    return kReleaseMode ? prodApiBaseUrl : devApiBaseUrl;
  }

  static const Duration networkTimeout = Duration(seconds: 30);
}
