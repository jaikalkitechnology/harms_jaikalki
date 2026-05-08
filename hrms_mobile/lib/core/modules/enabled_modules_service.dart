import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Caches the per-employee module whitelist served by
/// `GET /api/v1/me/enabled-modules`. The mobile More menu reads
/// `enabled` to decide which tiles to render.
///
/// Default behaviour when the service hasn't been hydrated yet (e.g.
/// fresh install, no network) is to expose `null`, which the More menu
/// treats as "show everything" so we never accidentally hide modules
/// from the user when the call fails.
class EnabledModulesService extends ChangeNotifier {
  EnabledModulesService(this._dio, this._prefs);

  static const _cacheKey = 'enabled_modules.v1';
  final Dio _dio;
  final SharedPreferences _prefs;

  Set<String>? _enabled;

  /// `null` until the first refresh / hydrate call succeeds.
  Set<String>? get enabled => _enabled;

  /// Returns true when [key] should be visible. When the service hasn't
  /// hydrated yet OR the user has no department restriction, returns
  /// true so we don't hide UI we can't gate yet.
  bool isEnabled(String key) {
    final s = _enabled;
    if (s == null) return true;
    return s.contains(key);
  }

  Future<void> hydrate() async {
    final cached = _prefs.getStringList(_cacheKey);
    if (cached != null) {
      _enabled = cached.toSet();
      notifyListeners();
    }
    // Fire-and-forget refresh in the background so UI doesn't block.
    refresh();
  }

  Future<void> refresh() async {
    try {
      final res = await _dio.get<Map<String, dynamic>>(
        '/api/v1/me/enabled-modules',
      );
      final raw = (res.data?['enabled'] as List?) ?? const [];
      final next = raw.map((e) => e.toString()).toSet();
      _enabled = next;
      await _prefs.setStringList(_cacheKey, next.toList());
      notifyListeners();
    } catch (_) {
      // Keep whatever cache we already had; silently ignore failures so
      // an offline launch still renders the menu.
    }
  }

  Future<void> clear() async {
    _enabled = null;
    await _prefs.remove(_cacheKey);
    notifyListeners();
  }
}
