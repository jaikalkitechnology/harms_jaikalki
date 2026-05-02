import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app.dart';
import 'core/di/injection.dart';
import 'core/push/push_notifications_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.dark);
  await setupDependencies();
  // Boot Firebase + push notifications. Failures don't block the UI;
  // the service falls back to in-app + email until Firebase is reachable.
  await PushNotificationsService.instance.initialize();
  runApp(const JaikalkiApp());
}
