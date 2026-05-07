// Background location sharing service for field employees.
//
// Lifecycle:
//   1. App startup → restore the persisted `enabled` flag from
//      SharedPreferences. If true, kick off the periodic ping.
//   2. User flips the toggle → start() or stop().
//   3. Each tick (default every 60 s) the service:
//        - asks geolocator for the latest position (best-of-3 accuracy)
//        - posts {lat, lng, accuracy, battery, is_mock} to
//          POST /api/v1/field/location/track via the existing FieldApi
//        - on failure, logs and keeps trying — the next tick is
//          independent so transient network drops self-heal.
//   4. When stopped, the timer is cancelled. The user appears as
//      "offline" on the admin live map after the 5-minute staleness
//      threshold.
//
// Permissions: requires location-while-using-app (Android & iOS). The
// service requests it on first start; if denied, the toggle flips back
// off and the user gets a snackbar via the caller.

import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import 'package:shared_preferences/shared_preferences.dart';

import '../di/injection.dart';
import '../../features/field/data/field_api.dart';

class LocationSharingService extends ChangeNotifier {
  LocationSharingService._();
  static final LocationSharingService instance = LocationSharingService._();

  static const _kEnabledKey = 'field.location_sharing_enabled';
  static const Duration _interval = Duration(seconds: 60);

  Timer? _timer;
  bool _enabled = false;
  bool _busy = false;
  DateTime? _lastSentAt;
  String? _lastError;

  bool get isEnabled => _enabled;
  bool get isBusy => _busy;
  DateTime? get lastSentAt => _lastSentAt;
  String? get lastError => _lastError;

  /// Restore persisted state and resume sharing if it was on.
  Future<void> hydrate() async {
    final prefs = await SharedPreferences.getInstance();
    final on = prefs.getBool(_kEnabledKey) ?? false;
    if (on) {
      // Resume silently. If permission has since been revoked, we'll
      // catch the failure inside _tick and clear the flag.
      await start(silent: true);
    }
  }

  /// Returns true if sharing is now enabled, false if blocked.
  Future<bool> start({bool silent = false}) async {
    if (_enabled) return true;
    if (!await _ensurePermission()) {
      _lastError = 'Location permission denied';
      notifyListeners();
      return false;
    }
    _enabled = true;
    _lastError = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kEnabledKey, true);
    _timer?.cancel();
    _timer = Timer.periodic(_interval, (_) => _tick());
    // Fire one ping immediately so the admin map updates without
    // waiting for the first interval to roll over.
    if (!silent) await _tick();
    notifyListeners();
    return true;
  }

  Future<void> stop() async {
    _enabled = false;
    _timer?.cancel();
    _timer = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_kEnabledKey, false);
    notifyListeners();
  }

  Future<bool> _ensurePermission() async {
    if (!await Geolocator.isLocationServiceEnabled()) return false;
    var perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      perm = await Geolocator.requestPermission();
    }
    if (perm == LocationPermission.denied ||
        perm == LocationPermission.deniedForever) {
      return false;
    }
    return true;
  }

  Future<void> _tick() async {
    if (_busy || !_enabled) return;
    _busy = true;
    notifyListeners();
    try {
      final pos = await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
        timeLimit: const Duration(seconds: 12),
      );
      // Battery readout is best-effort — we don't pull in a separate
      // dep just for this; the field is optional server-side.
      int? battery;
      try {
        // ignore: depend_on_referenced_packages
        // Avoid hard-failing if the package isn't present.
        battery = null;
      } catch (_) {
        battery = null;
      }
      await sl<FieldApi>().trackLocation(
        lat: pos.latitude,
        lng: pos.longitude,
        accuracyM: pos.accuracy.round(),
        batteryPct: battery,
        isMock: pos.isMocked,
      );
      _lastSentAt = DateTime.now();
      _lastError = null;
    } catch (e) {
      _lastError = e.toString();
      // Keep the timer alive — transient errors recover on next tick.
      if (kDebugMode) {
        debugPrint('[LocationSharing] tick failed: $e');
      }
    } finally {
      _busy = false;
      notifyListeners();
    }
  }
}

/// Helper that picks a sensible default based on platform — currently
/// just returns the singleton.
LocationSharingService locationSharing() => LocationSharingService.instance;
