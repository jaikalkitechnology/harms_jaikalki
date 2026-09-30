import 'dart:convert';

import '../../../../core/storage/secure_storage.dart';
import '../../domain/entities/auth_user.dart';
import '../../domain/entities/token_pair.dart';
import '../../domain/repositories/auth_repository.dart';
import '../datasources/auth_remote_datasource.dart';
import '../models/user_model.dart';

class AuthRepositoryImpl implements AuthRepository {
  AuthRepositoryImpl({
    required AuthRemoteDataSource remote,
    required SecureStorage storage,
  })  : _remote = remote,
        _storage = storage;

  final AuthRemoteDataSource _remote;
  final SecureStorage _storage;

  @override
  Future<TokenPair> login({
    required String email,
    required String password,
    bool rememberMe = false,
  }) async {
    final response = await _remote.login(
      email: email,
      password: password,
      rememberMe: rememberMe,
    );
    final pair = response.toEntity();
    await _storage.writeAccessToken(pair.accessToken);
    await _storage.writeRefreshToken(pair.refreshToken);
    return pair;
  }

  @override
  Future<TokenPair> refresh(String refreshToken) async {
    final response = await _remote.refresh(refreshToken);
    final pair = response.toEntity();
    await _storage.writeAccessToken(pair.accessToken);
    await _storage.writeRefreshToken(pair.refreshToken);
    return pair;
  }

  @override
  Future<void> logout() async {
    final refresh = await _storage.readRefreshToken();
    if (refresh != null && refresh.isNotEmpty) {
      try {
        await _remote.logout(refresh);
      } catch (_) {
        // Ignore network errors during logout — still clear local state.
      }
    }
    await _storage.clear();
  }

  @override
  Future<AuthUser> me() async {
    final user = (await _remote.me()).toEntity();
    try {
      await _storage.writeCachedUser(jsonEncode(MeResponseModel.toJson(user)));
    } catch (_) {
      // The cache is best-effort.
    }
    return user;
  }

  @override
  Future<AuthUser?> cachedUser() async {
    final raw = await _storage.readCachedUser();
    if (raw == null || raw.isEmpty) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return MeResponseModel.fromJson(json).toEntity();
    } catch (_) {
      return null;
    }
  }

  @override
  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) =>
      _remote.changePassword(
        oldPassword: oldPassword,
        newPassword: newPassword,
      );
}
