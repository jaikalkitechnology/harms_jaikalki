import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'app.dart';
import 'core/di/injection.dart';
import 'core/location/location_sharing_service.dart';
import 'core/modules/enabled_modules_service.dart';
import 'core/push/push_notifications_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.dark);
  await setupDependencies();
  // Boot Firebase + push notifications. Failures don't block the UI;
  // the service falls back to in-app + email until Firebase is reachable.
  await PushNotificationsService.instance.initialize();
  // Resume background location sharing if the user had it on.
  // Failure is silent — the toggle stays off until they re-enable.
  await LocationSharingService.instance.hydrate();
  // Hydrate per-department module whitelist from cache; an async
  // refresh is fired in the background and the More menu rebuilds when
  // it lands.
  await sl<EnabledModulesService>().hydrate();
  runApp(const JaikalkiApp());
}
