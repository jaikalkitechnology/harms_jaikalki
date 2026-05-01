import '../entities/token_pair.dart';
import '../repositories/auth_repository.dart';

class RefreshTokenUseCase {
  RefreshTokenUseCase(this._repo);
  final AuthRepository _repo;

  Future<TokenPair> call(String refreshToken) => _repo.refresh(refreshToken);
}
