import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  SecureStorage(this._storage);

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';
  static const _bioKey = 'biometric_enabled';
  static const _userKey = 'cached_user';

  final FlutterSecureStorage _storage;

  /// A read that can't take the app down. Android can lose the keystore
  /// key (e.g. after a backup restore), making stored values
  /// undecryptable; treat that as "nothing stored" instead of crashing
  /// the start-up auth check.
  Future<String?> _read(String key) async {
    try {
      return await _storage.read(key: key);
    } catch (e) {
      debugPrint('SecureStorage: read "$key" failed: $e');
      return null;
    }
  }

  Future<void> writeAccessToken(String token) =>
      _storage.write(key: _accessKey, value: token);

  Future<String?> readAccessToken() => _read(_accessKey);

  Future<void> writeRefreshToken(String token) =>
      _storage.write(key: _refreshKey, value: token);

  Future<String?> readRefreshToken() => _read(_refreshKey);

  Future<void> setBiometricEnabled(bool enabled) =>
      _storage.write(key: _bioKey, value: enabled ? '1' : '0');

  Future<bool> isBiometricEnabled() async => (await _read(_bioKey)) == '1';

  /// Last `/auth/me` response (JSON), so the app can open signed in
  /// while the server is unreachable.
  Future<void> writeCachedUser(String json) =>
      _storage.write(key: _userKey, value: json);

  Future<String?> readCachedUser() => _read(_userKey);

  /// Small per-user caches (e.g. the last dashboard). Living here means
  /// a full sign-out — which wipes this storage — removes them too.
  Future<void> writeCache(String name, String json) =>
      _storage.write(key: 'cache.$name', value: json);

  Future<String?> readCache(String name) => _read('cache.$name');

  /// Soft sign-out: drop only the access token, keeping the
  /// biometric-protected refresh token + flag so the user can come
  /// back in via fingerprint/Face ID without retyping the password.
  Future<void> clearAccessToken() => _storage.delete(key: _accessKey);

  Future<void> clear() async {
    try {
      await _storage.deleteAll();
    } catch (e) {
      debugPrint('SecureStorage: clear failed: $e');
    }
  }
}
