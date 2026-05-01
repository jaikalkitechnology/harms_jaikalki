import '../entities/auth_user.dart';
import '../entities/token_pair.dart';

abstract class AuthRepository {
  Future<TokenPair> login({
    required String email,
    required String password,
    bool rememberMe = false,
  });

  Future<AuthUser> me();

  Future<TokenPair> refresh(String refreshToken);

  Future<void> logout();

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  });
}
