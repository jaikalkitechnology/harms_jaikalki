import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorage {
  SecureStorage(this._storage);

  static const _accessKey = 'access_token';
  static const _refreshKey = 'refresh_token';

  final FlutterSecureStorage _storage;

  Future<void> writeAccessToken(String token) =>
      _storage.write(key: _accessKey, value: token);

  Future<String?> readAccessToken() => _storage.read(key: _accessKey);

  Future<void> writeRefreshToken(String token) =>
      _storage.write(key: _refreshKey, value: token);

  Future<String?> readRefreshToken() => _storage.read(key: _refreshKey);

  Future<void> clear() => _storage.deleteAll();
}
