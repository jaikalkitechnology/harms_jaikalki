// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppL10nEn extends AppL10n {
  AppL10nEn([String locale = 'en']) : super(locale);

  @override
  String get appName => 'Jaikalki HRMS';

  @override
  String get welcomeBack => 'Welcome back';

  @override
  String get signIn => 'Sign in';

  @override
  String get email => 'Email';

  @override
  String get password => 'Password';

  @override
  String get rememberMe => 'Remember me';

  @override
  String get forgotPassword => 'Forgot password?';

  @override
  String get useBiometrics => 'Use biometrics';

  @override
  String get signOut => 'Sign out';

  @override
  String get home => 'Home';

  @override
  String get approvals => 'Approvals';

  @override
  String get attendance => 'Attendance';

  @override
  String get leaves => 'Leaves';

  @override
  String get more => 'More';

  @override
  String get profile => 'Profile';

  @override
  String get settings => 'Settings';

  @override
  String get language => 'Language';

  @override
  String get theme => 'Theme';

  @override
  String get themeLight => 'Light';

  @override
  String get themeDark => 'Dark';

  @override
  String get themeSystem => 'System default';

  @override
  String get english => 'English';

  @override
  String get hindi => 'हिन्दी';

  @override
  String get today => 'Today';

  @override
  String get checkIn => 'Check in';

  @override
  String get checkOut => 'Check out';

  @override
  String get wfhCheckIn => 'WFH check-in';

  @override
  String get leaveBalance => 'Leave balance';

  @override
  String get applyLeave => 'Apply leave';

  @override
  String get approve => 'Approve';

  @override
  String get reject => 'Reject';

  @override
  String get employees => 'Employees';

  @override
  String get documents => 'Documents';

  @override
  String get orgChart => 'Org chart';

  @override
  String get help => 'Help';

  @override
  String get version => 'Version';

  @override
  String get appVersion => 'App version';

  @override
  String get biometric => 'Biometric login';

  @override
  String get notifications => 'Notifications';

  @override
  String get privacyPolicy => 'Privacy policy';

  @override
  String get aboutApp => 'About this app';

  @override
  String get logout => 'Log out';

  @override
  String get logoutConfirm => 'Are you sure you want to sign out?';

  @override
  String get cancel => 'Cancel';

  @override
  String get ok => 'OK';

  @override
  String get noConnection => 'No internet connection';

  @override
  String get retry => 'Retry';

  @override
  String get somethingWentWrong => 'Something went wrong';

  @override
  String get tryAgain => 'Try again';

  @override
  String get onboardingTitle1 => 'All-in-one HR';

  @override
  String get onboardingBody1 =>
      'Attendance, leaves, payroll and approvals — all from your phone.';

  @override
  String get onboardingTitle2 => 'Geo-fenced check-in';

  @override
  String get onboardingBody2 =>
      'Mark your attendance with one tap when you reach the office.';

  @override
  String get onboardingTitle3 => 'Stay in the loop';

  @override
  String get onboardingBody3 => 'Approvals come to you. Decide on the go.';

  @override
  String get onboardingNext => 'Next';

  @override
  String get onboardingDone => 'Get started';

  @override
  String get loading => 'Loading…';

  @override
  String get noData => 'Nothing to show.';

  @override
  String get headcount => 'Headcount';

  @override
  String get teamAttendance => 'Team attendance';

  @override
  String get pendingApprovals => 'Pending approvals';

  @override
  String get birthdaysThisWeek => 'Birthdays this week';

  @override
  String get probationExpiring => 'Probation ending soon';

  @override
  String get nextPayday => 'Next payday';

  @override
  String daysToPayday(int n) {
    return '$n days';
  }
}
