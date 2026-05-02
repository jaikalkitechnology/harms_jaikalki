// Firebase Cloud Messaging integration.
//
// Lifecycle:
// 1.  `initialize()` is called from main.dart before runApp(). It boots
//     Firebase, requests permission, sets up the local-notifications
//     channel that we use to render foreground messages, and wires the
//     three message handlers (foreground / background / terminated).
//
// 2.  After login, `registerToken(api)` is called from AuthBloc once the
//     user is authenticated, so device tokens are stored against a real
//     user. It listens for token refreshes too.
//
// 3.  `unregisterToken(api)` runs on logout to deactivate the token
//     server-side without forcing the user to delete the FCM identifier.
//
// All `data` payloads are forwarded to the local-notifications channel
// so taps can deep-link into a route via the global navigator.

import 'dart:async';
import 'dart:convert';
import 'dart:io' show Platform;

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../../features/launch/data/launch_api.dart';
import '../di/injection.dart';

/// Top-level — required by the FlutterFire background-handler contract.
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  // The OS owns the notification banner here; we just log so the entry
  // point doesn't get tree-shaken in release builds.
  debugPrint('[FCM bg] ${message.messageId} ${message.data}');
}

class PushNotificationsService {
  PushNotificationsService._();
  static final PushNotificationsService instance =
      PushNotificationsService._();

  final FlutterLocalNotificationsPlugin _local =
      FlutterLocalNotificationsPlugin();
  final FirebaseMessaging _fcm = FirebaseMessaging.instance;

  static const _androidChannel = AndroidNotificationChannel(
    'jaikalki_default',
    'Jaikalki HRMS',
    description:
        'Approvals, reminders, exam results, and other workplace updates.',
    importance: Importance.high,
  );

  static const _kLastTokenKey = 'fcm_last_token';

  bool _initialised = false;

  /// Boot Firebase + local-notifications. Safe to call once at app start;
  /// no-op on repeat. Catches any Firebase error so the app keeps running
  /// even if the device hasn't been added to the Firebase console yet.
  Future<void> initialize({GlobalKey<NavigatorState>? navigatorKey}) async {
    if (_initialised) return;
    try {
      await Firebase.initializeApp();

      await _fcm.setForegroundNotificationPresentationOptions(
        alert: true,
        badge: true,
        sound: true,
      );

      // Permission prompts (iOS + Android 13+).
      await _fcm.requestPermission(alert: true, badge: true, sound: true);

      // Local notifications channel — used to render foreground messages
      // ourselves since FCM only auto-banners when the app is backgrounded.
      const initSettings = InitializationSettings(
        android: AndroidInitializationSettings('@mipmap/ic_launcher'),
        iOS: DarwinInitializationSettings(
          requestAlertPermission: true,
          requestBadgePermission: true,
          requestSoundPermission: true,
        ),
      );
      await _local.initialize(
        initSettings,
        onDidReceiveNotificationResponse: (response) {
          final payload = response.payload;
          if (payload != null) {
            _handleTap(jsonDecode(payload) as Map<String, dynamic>,
                navigatorKey: navigatorKey);
          }
        },
      );
      await _local
          .resolvePlatformSpecificImplementation<
              AndroidFlutterLocalNotificationsPlugin>()
          ?.createNotificationChannel(_androidChannel);

      // Register the background handler before the foreground listener so
      // the OS can wake us up from a terminated state.
      FirebaseMessaging.onBackgroundMessage(
        _firebaseMessagingBackgroundHandler,
      );

      // Foreground messages arrive here — we render them via the local
      // plugin since the OS won't show a banner for an open app.
      FirebaseMessaging.onMessage.listen((m) => _showLocal(m));

      // Tap on a notification while the app was backgrounded.
      FirebaseMessaging.onMessageOpenedApp.listen(
        (m) => _handleTap(m.data, navigatorKey: navigatorKey),
      );

      // The message that launched a terminated app, if any.
      final initial = await _fcm.getInitialMessage();
      if (initial != null) {
        _handleTap(initial.data, navigatorKey: navigatorKey);
      }

      _initialised = true;
      debugPrint('[FCM] initialised');
    } catch (e, st) {
      debugPrint('[FCM] init failed: $e\n$st');
    }
  }

  /// Push the FCM device token to the backend so the server can target
  /// this device. Listens for token refreshes too. Idempotent — we cache
  /// the last token in SharedPreferences and skip the network call if
  /// nothing changed.
  Future<void> registerToken(LaunchApi api) async {
    if (!_initialised) return;
    try {
      final token = await _fcm.getToken();
      if (token == null) return;
      final prefs = await SharedPreferences.getInstance();
      if (prefs.getString(_kLastTokenKey) == token) return;

      final platform = Platform.isAndroid
          ? 'android'
          : Platform.isIOS
              ? 'ios'
              : 'web';
      await api.registerDeviceToken(platform: platform, token: token);
      await prefs.setString(_kLastTokenKey, token);
      debugPrint('[FCM] token registered');

      // Token can rotate on app reinstall, OS update, etc.
      _fcm.onTokenRefresh.listen((newToken) async {
        try {
          await api.registerDeviceToken(platform: platform, token: newToken);
          await prefs.setString(_kLastTokenKey, newToken);
          debugPrint('[FCM] token refreshed');
        } catch (e) {
          debugPrint('[FCM] token refresh failed: $e');
        }
      });
    } catch (e) {
      debugPrint('[FCM] registerToken failed: $e');
    }
  }

  /// Best-effort: drop the token server-side and clear the cached copy.
  Future<void> unregisterToken(LaunchApi api) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString(_kLastTokenKey);
      await prefs.remove(_kLastTokenKey);
      await _fcm.deleteToken();
      // The launch_api expects DELETE /notifications/devices/{token} but
      // the simpler path is to just stop sending — server-side, the row
      // becomes stale and gets deactivated on the next failed multicast.
      // Wire a real DELETE here once the backend exposes it cleanly.
      if (token != null) debugPrint('[FCM] cleared token $token');
    } catch (e) {
      debugPrint('[FCM] unregisterToken failed: $e');
    }
  }

  Future<void> _showLocal(RemoteMessage m) async {
    final notif = m.notification;
    final title = notif?.title ?? m.data['title']?.toString() ?? 'Jaikalki HRMS';
    final body = notif?.body ?? m.data['body']?.toString() ?? '';
    await _local.show(
      m.hashCode,
      title,
      body,
      NotificationDetails(
        android: AndroidNotificationDetails(
          _androidChannel.id,
          _androidChannel.name,
          channelDescription: _androidChannel.description,
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
        iOS: const DarwinNotificationDetails(),
      ),
      payload: jsonEncode(m.data),
    );
  }

  void _handleTap(
    Map<String, dynamic> data, {
    GlobalKey<NavigatorState>? navigatorKey,
  }) {
    // Default routing: most server-side notify() calls embed `type` and
    // sometimes `route`. Adapt as you need — keep this small.
    final route = data['route']?.toString();
    if (route == null || navigatorKey == null) return;
    final state = navigatorKey.currentState;
    if (state == null) return;
    state.pushNamed(route);
  }
}
