import '../entities/token_pair.dart';
import '../repositories/auth_repository.dart';

class LoginParams {
  const LoginParams({
    required this.email,
    required this.password,
    this.rememberMe = false,
  });

  final String email;
  final String password;
  final bool rememberMe;
}

class Login {
  Login(this._repo);
  final AuthRepository _repo;

  Future<TokenPair> call(LoginParams p) => _repo.login(
        email: p.email,
        password: p.password,
        rememberMe: p.rememberMe,
      );
}
