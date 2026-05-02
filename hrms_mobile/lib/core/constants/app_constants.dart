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

  /// API base URL.
  ///
  /// Defaults to the live production backend in every build flavour
  /// (debug + release) so devices can reach the server out of the box.
  /// To point at a local backend, pass at run/build time:
  ///   --dart-define=API_BASE_URL=http://10.0.2.2:8000   (Android emu)
  ///   --dart-define=API_BASE_URL=http://localhost:8000  (iOS sim)
  static String get apiBaseUrl {
    const override = String.fromEnvironment('API_BASE_URL');
    return override.isNotEmpty ? override : prodApiBaseUrl;
  }

  static const Duration networkTimeout = Duration(seconds: 30);
}
