import 'dart:async';

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
  // Per-department module whitelist from cache (a local read); a refresh
  // runs in the background and the More menu rebuilds when it lands.
  await sl<EnabledModulesService>().hydrate();
  runApp(const JaikalkiApp());

  // Not needed for the first frame, so it no longer delays it. Push setup
  // waits on the notification-permission prompt the first time, and
  // location sharing on a GPS permission check.
  unawaited(PushNotificationsService.instance.initialize());
  unawaited(LocationSharingService.instance.hydrate());
}
