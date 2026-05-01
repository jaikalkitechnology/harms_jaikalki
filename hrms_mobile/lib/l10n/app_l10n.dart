import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

/// Hand-rolled, build-without-codegen localization layer.
///
/// The ARB files in `lib/l10n/app_en.arb` and `app_hi.arb` are the source of
/// truth and can be passed through `flutter gen-l10n` later for full
/// type-safe accessors. This stub keeps the same key set so the migration
/// is painless.
class AppL10n {
  AppL10n(this.locale);

  final Locale locale;

  static const supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
  ];

  static const localizationsDelegates = <LocalizationsDelegate<dynamic>>[
    _AppL10nDelegate(),
    GlobalMaterialLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
  ];

  static AppL10n of(BuildContext context) =>
      Localizations.of<AppL10n>(context, AppL10n) ?? AppL10n(const Locale('en'));

  String _t(String key) {
    final code = locale.languageCode;
    final fallback = _en[key] ?? key;
    if (code == 'hi') return _hi[key] ?? fallback;
    return fallback;
  }

  String get appName => _t('appName');
  String get welcomeBack => _t('welcomeBack');
  String get signIn => _t('signIn');
  String get email => _t('email');
  String get password => _t('password');
  String get rememberMe => _t('rememberMe');
  String get forgotPassword => _t('forgotPassword');
  String get useBiometrics => _t('useBiometrics');
  String get signOut => _t('signOut');
  String get home => _t('home');
  String get approvals => _t('approvals');
  String get attendance => _t('attendance');
  String get leaves => _t('leaves');
  String get more => _t('more');
  String get profile => _t('profile');
  String get settings => _t('settings');
  String get language => _t('language');
  String get theme => _t('theme');
  String get themeLight => _t('themeLight');
  String get themeDark => _t('themeDark');
  String get themeSystem => _t('themeSystem');
  String get english => _t('english');
  String get hindi => _t('hindi');
  String get today => _t('today');
  String get checkIn => _t('checkIn');
  String get checkOut => _t('checkOut');
  String get wfhCheckIn => _t('wfhCheckIn');
  String get leaveBalance => _t('leaveBalance');
  String get applyLeave => _t('applyLeave');
  String get approve => _t('approve');
  String get reject => _t('reject');
  String get employees => _t('employees');
  String get documents => _t('documents');
  String get orgChart => _t('orgChart');
  String get help => _t('help');
  String get version => _t('version');
  String get appVersion => _t('appVersion');
  String get biometric => _t('biometric');
  String get notifications => _t('notifications');
  String get privacyPolicy => _t('privacyPolicy');
  String get aboutApp => _t('aboutApp');
  String get logout => _t('logout');
  String get logoutConfirm => _t('logoutConfirm');
  String get cancel => _t('cancel');
  String get ok => _t('ok');
  String get noConnection => _t('noConnection');
  String get retry => _t('retry');
  String get somethingWentWrong => _t('somethingWentWrong');
  String get tryAgain => _t('tryAgain');
  String get onboardingTitle1 => _t('onboardingTitle1');
  String get onboardingBody1 => _t('onboardingBody1');
  String get onboardingTitle2 => _t('onboardingTitle2');
  String get onboardingBody2 => _t('onboardingBody2');
  String get onboardingTitle3 => _t('onboardingTitle3');
  String get onboardingBody3 => _t('onboardingBody3');
  String get onboardingNext => _t('onboardingNext');
  String get onboardingDone => _t('onboardingDone');
  String get loading => _t('loading');
  String get noData => _t('noData');
  String get headcount => _t('headcount');
  String get teamAttendance => _t('teamAttendance');
  String get pendingApprovals => _t('pendingApprovals');
  String get birthdaysThisWeek => _t('birthdaysThisWeek');
  String get probationExpiring => _t('probationExpiring');
  String get nextPayday => _t('nextPayday');

  String daysToPayday(int n) {
    if (locale.languageCode == 'hi') return '$n दिन';
    return '$n days';
  }
}

class _AppL10nDelegate extends LocalizationsDelegate<AppL10n> {
  const _AppL10nDelegate();

  @override
  bool isSupported(Locale locale) =>
      AppL10n.supportedLocales
          .any((l) => l.languageCode == locale.languageCode);

  @override
  Future<AppL10n> load(Locale locale) async => AppL10n(locale);

  @override
  bool shouldReload(_AppL10nDelegate old) => false;
}

const Map<String, String> _en = {
  'appName': 'Jaikalki HRMS',
  'welcomeBack': 'Welcome back',
  'signIn': 'Sign in',
  'email': 'Email',
  'password': 'Password',
  'rememberMe': 'Remember me',
  'forgotPassword': 'Forgot password?',
  'useBiometrics': 'Use biometrics',
  'signOut': 'Sign out',
  'home': 'Home',
  'approvals': 'Approvals',
  'attendance': 'Attendance',
  'leaves': 'Leaves',
  'more': 'More',
  'profile': 'Profile',
  'settings': 'Settings',
  'language': 'Language',
  'theme': 'Theme',
  'themeLight': 'Light',
  'themeDark': 'Dark',
  'themeSystem': 'System default',
  'english': 'English',
  'hindi': 'हिन्दी',
  'today': 'Today',
  'checkIn': 'Check in',
  'checkOut': 'Check out',
  'wfhCheckIn': 'WFH check-in',
  'leaveBalance': 'Leave balance',
  'applyLeave': 'Apply leave',
  'approve': 'Approve',
  'reject': 'Reject',
  'employees': 'Employees',
  'documents': 'Documents',
  'orgChart': 'Org chart',
  'help': 'Help',
  'version': 'Version',
  'appVersion': 'App version',
  'biometric': 'Biometric login',
  'notifications': 'Notifications',
  'privacyPolicy': 'Privacy policy',
  'aboutApp': 'About this app',
  'logout': 'Log out',
  'logoutConfirm': 'Are you sure you want to sign out?',
  'cancel': 'Cancel',
  'ok': 'OK',
  'noConnection': 'No internet connection',
  'retry': 'Retry',
  'somethingWentWrong': 'Something went wrong',
  'tryAgain': 'Try again',
  'onboardingTitle1': 'All-in-one HR',
  'onboardingBody1':
      'Attendance, leaves, payroll and approvals — all from your phone.',
  'onboardingTitle2': 'Geo-fenced check-in',
  'onboardingBody2':
      'Mark your attendance with one tap when you reach the office.',
  'onboardingTitle3': 'Stay in the loop',
  'onboardingBody3': 'Approvals come to you. Decide on the go.',
  'onboardingNext': 'Next',
  'onboardingDone': 'Get started',
  'loading': 'Loading…',
  'noData': 'Nothing to show.',
  'headcount': 'Headcount',
  'teamAttendance': 'Team attendance',
  'pendingApprovals': 'Pending approvals',
  'birthdaysThisWeek': 'Birthdays this week',
  'probationExpiring': 'Probation ending soon',
  'nextPayday': 'Next payday',
};

const Map<String, String> _hi = {
  'appName': 'जयकल्की HRMS',
  'welcomeBack': 'वापसी पर स्वागत है',
  'signIn': 'साइन इन',
  'email': 'ईमेल',
  'password': 'पासवर्ड',
  'rememberMe': 'मुझे याद रखें',
  'forgotPassword': 'पासवर्ड भूल गए?',
  'useBiometrics': 'बायोमेट्रिक उपयोग करें',
  'signOut': 'साइन आउट',
  'home': 'होम',
  'approvals': 'मंज़ूरी',
  'attendance': 'उपस्थिति',
  'leaves': 'अवकाश',
  'more': 'और',
  'profile': 'प्रोफ़ाइल',
  'settings': 'सेटिंग्स',
  'language': 'भाषा',
  'theme': 'थीम',
  'themeLight': 'लाइट',
  'themeDark': 'डार्क',
  'themeSystem': 'सिस्टम डिफ़ॉल्ट',
  'today': 'आज',
  'checkIn': 'चेक-इन',
  'checkOut': 'चेक-आउट',
  'wfhCheckIn': 'WFH चेक-इन',
  'leaveBalance': 'अवकाश शेष',
  'applyLeave': 'अवकाश के लिए आवेदन',
  'approve': 'स्वीकार',
  'reject': 'अस्वीकार',
  'employees': 'कर्मचारी',
  'documents': 'दस्तावेज़',
  'orgChart': 'संगठन चार्ट',
  'help': 'सहायता',
  'version': 'संस्करण',
  'appVersion': 'ऐप संस्करण',
  'biometric': 'बायोमेट्रिक लॉगिन',
  'notifications': 'सूचनाएँ',
  'privacyPolicy': 'गोपनीयता नीति',
  'aboutApp': 'इस ऐप के बारे में',
  'logout': 'लॉग आउट',
  'logoutConfirm': 'क्या आप वाकई साइन आउट करना चाहते हैं?',
  'cancel': 'रद्द',
  'ok': 'ठीक है',
  'noConnection': 'इंटरनेट कनेक्शन नहीं है',
  'retry': 'पुनः प्रयास',
  'somethingWentWrong': 'कुछ गलत हो गया',
  'tryAgain': 'पुनः प्रयास करें',
  'onboardingTitle1': 'सम्पूर्ण HR',
  'onboardingBody1': 'उपस्थिति, अवकाश, वेतन और मंज़ूरी — सब फ़ोन से।',
  'onboardingTitle2': 'जियो-फेंस चेक-इन',
  'onboardingBody2': 'ऑफ़िस पहुँचते ही एक टैप से उपस्थिति दर्ज करें।',
  'onboardingTitle3': 'अपडेट रहें',
  'onboardingBody3': 'मंज़ूरी सीधे आपके पास आती है। तुरंत निर्णय लें।',
  'onboardingNext': 'आगे',
  'onboardingDone': 'शुरू करें',
  'loading': 'लोड हो रहा है…',
  'noData': 'दिखाने के लिए कुछ नहीं।',
  'headcount': 'कुल कर्मचारी',
  'teamAttendance': 'टीम उपस्थिति',
  'pendingApprovals': 'लंबित मंज़ूरी',
  'birthdaysThisWeek': 'इस सप्ताह जन्मदिन',
  'probationExpiring': 'जल्द समाप्त होने वाला परिवीक्षा',
  'nextPayday': 'अगला वेतन दिवस',
};
