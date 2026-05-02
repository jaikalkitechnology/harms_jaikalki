// ignore: unused_import
import 'package:intl/intl.dart' as intl;
import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppL10nHi extends AppL10n {
  AppL10nHi([String locale = 'hi']) : super(locale);

  @override
  String get appName => 'जयकल्की HRMS';

  @override
  String get welcomeBack => 'वापसी पर स्वागत है';

  @override
  String get signIn => 'साइन इन';

  @override
  String get email => 'ईमेल';

  @override
  String get password => 'पासवर्ड';

  @override
  String get rememberMe => 'मुझे याद रखें';

  @override
  String get forgotPassword => 'पासवर्ड भूल गए?';

  @override
  String get useBiometrics => 'बायोमेट्रिक उपयोग करें';

  @override
  String get signOut => 'साइन आउट';

  @override
  String get home => 'होम';

  @override
  String get approvals => 'मंज़ूरी';

  @override
  String get attendance => 'उपस्थिति';

  @override
  String get leaves => 'अवकाश';

  @override
  String get more => 'और';

  @override
  String get profile => 'प्रोफ़ाइल';

  @override
  String get settings => 'सेटिंग्स';

  @override
  String get language => 'भाषा';

  @override
  String get theme => 'थीम';

  @override
  String get themeLight => 'लाइट';

  @override
  String get themeDark => 'डार्क';

  @override
  String get themeSystem => 'सिस्टम डिफ़ॉल्ट';

  @override
  String get english => 'English';

  @override
  String get hindi => 'हिन्दी';

  @override
  String get today => 'आज';

  @override
  String get checkIn => 'चेक-इन';

  @override
  String get checkOut => 'चेक-आउट';

  @override
  String get wfhCheckIn => 'WFH चेक-इन';

  @override
  String get leaveBalance => 'अवकाश शेष';

  @override
  String get applyLeave => 'अवकाश के लिए आवेदन करें';

  @override
  String get approve => 'स्वीकार';

  @override
  String get reject => 'अस्वीकार';

  @override
  String get employees => 'कर्मचारी';

  @override
  String get documents => 'दस्तावेज़';

  @override
  String get orgChart => 'संगठन चार्ट';

  @override
  String get help => 'सहायता';

  @override
  String get version => 'संस्करण';

  @override
  String get appVersion => 'ऐप संस्करण';

  @override
  String get biometric => 'बायोमेट्रिक लॉगिन';

  @override
  String get notifications => 'सूचनाएँ';

  @override
  String get privacyPolicy => 'गोपनीयता नीति';

  @override
  String get aboutApp => 'इस ऐप के बारे में';

  @override
  String get logout => 'लॉग आउट';

  @override
  String get logoutConfirm => 'क्या आप वाकई साइन आउट करना चाहते हैं?';

  @override
  String get cancel => 'रद्द';

  @override
  String get ok => 'ठीक है';

  @override
  String get noConnection => 'इंटरनेट कनेक्शन नहीं है';

  @override
  String get retry => 'पुनः प्रयास';

  @override
  String get somethingWentWrong => 'कुछ गलत हो गया';

  @override
  String get tryAgain => 'पुनः प्रयास करें';

  @override
  String get onboardingTitle1 => 'सम्पूर्ण HR';

  @override
  String get onboardingBody1 =>
      'उपस्थिति, अवकाश, वेतन और मंज़ूरी — सब फ़ोन से।';

  @override
  String get onboardingTitle2 => 'जियो-फेंस चेक-इन';

  @override
  String get onboardingBody2 =>
      'ऑफ़िस पहुँचते ही एक टैप से उपस्थिति दर्ज करें।';

  @override
  String get onboardingTitle3 => 'अपडेट रहें';

  @override
  String get onboardingBody3 =>
      'मंज़ूरी सीधे आपके पास आती है। तुरंत निर्णय लें।';

  @override
  String get onboardingNext => 'आगे';

  @override
  String get onboardingDone => 'शुरू करें';

  @override
  String get loading => 'लोड हो रहा है…';

  @override
  String get noData => 'दिखाने के लिए कुछ नहीं।';

  @override
  String get headcount => 'कुल कर्मचारी';

  @override
  String get teamAttendance => 'टीम उपस्थिति';

  @override
  String get pendingApprovals => 'लंबित मंज़ूरी';

  @override
  String get birthdaysThisWeek => 'इस सप्ताह जन्मदिन';

  @override
  String get probationExpiring => 'जल्द समाप्त होने वाला परिवीक्षा';

  @override
  String get nextPayday => 'अगला वेतन दिवस';

  @override
  String daysToPayday(int n) {
    return '$n दिन';
  }
}
