class AppConstants {
  AppConstants._();

  static const String appName = 'Jaikalki HRMS';
  static const String companyName = 'Jaikalki Technology Pvt Ltd';
  static const String companyAddress =
      'Sh N B1/A Ground Floor, Mahavir Nagar, Deepak Hospital, '
      'Mira Road, Thane-401107 Maharashtra';
  static const String employeeCodePrefix = 'JKT';

  static const String apiBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');

  static const Duration networkTimeout = Duration(seconds: 30);
}
