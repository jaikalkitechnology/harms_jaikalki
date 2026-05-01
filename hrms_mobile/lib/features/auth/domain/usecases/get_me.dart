import '../entities/auth_user.dart';
import '../repositories/auth_repository.dart';

class GetMe {
  GetMe(this._repo);
  final AuthRepository _repo;

  Future<AuthUser> call() => _repo.me();
}
