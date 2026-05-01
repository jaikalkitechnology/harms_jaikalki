import 'package:bloc/bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:local_auth/local_auth.dart';

import '../../../../core/storage/secure_storage.dart';
import '../../domain/entities/auth_user.dart';
import '../../domain/repositories/auth_repository.dart';

part 'auth_event.dart';
part 'auth_state.dart';

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc({
    required AuthRepository repository,
    required SecureStorage storage,
    LocalAuthentication? localAuth,
  })  : _repository = repository,
        _storage = storage,
        _localAuth = localAuth ?? LocalAuthentication(),
        super(const AuthState.initial()) {
    on<AuthCheckRequested>(_onCheck);
    on<AuthLoginRequested>(_onLogin);
    on<AuthBiometricLoginRequested>(_onBiometricLogin);
    on<AuthLogoutRequested>(_onLogout);
    on<AuthTokenRefreshRequested>(_onRefresh);
  }

  final AuthRepository _repository;
  final SecureStorage _storage;
  final LocalAuthentication _localAuth;

  Future<void> _onCheck(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(state.copyWith(status: AuthStatus.loading, clearError: true));
    final access = await _storage.readAccessToken();
    if (access == null || access.isEmpty) {
      emit(state.copyWith(
        status: AuthStatus.unauthenticated,
        clearUser: true,
      ));
      return;
    }
    try {
      final user = await _repository.me();
      emit(state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      ));
    } catch (_) {
      await _storage.clear();
      emit(state.copyWith(
        status: AuthStatus.unauthenticated,
        clearUser: true,
      ));
    }
  }

  Future<void> _onLogin(
    AuthLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(state.copyWith(status: AuthStatus.loading, clearError: true));
    try {
      await _repository.login(
        email: event.email,
        password: event.password,
        rememberMe: event.rememberMe,
      );
      final user = await _repository.me();
      emit(state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      ));
    } catch (e) {
      emit(state.copyWith(
        status: AuthStatus.error,
        errorMessage: _humanize(e),
        clearUser: true,
      ));
    }
  }

  Future<void> _onBiometricLogin(
    AuthBiometricLoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    try {
      final canCheck = await _localAuth.canCheckBiometrics;
      if (!canCheck) {
        emit(state.copyWith(
          status: AuthStatus.error,
          errorMessage: 'Biometrics not available on this device',
        ));
        return;
      }
      final ok = await _localAuth.authenticate(
        localizedReason: 'Sign in to Jaikalki HRMS',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
        ),
      );
      if (!ok) {
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          errorMessage: 'Biometric auth cancelled',
        ));
        return;
      }
      // Reuse existing access token; if expired the interceptor will refresh.
      final access = await _storage.readAccessToken();
      if (access == null || access.isEmpty) {
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          errorMessage: 'No saved credentials. Sign in with password first.',
        ));
        return;
      }
      add(const AuthCheckRequested());
    } catch (e) {
      emit(state.copyWith(
        status: AuthStatus.error,
        errorMessage: _humanize(e),
      ));
    }
  }

  Future<void> _onLogout(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    await _repository.logout();
    emit(const AuthState(status: AuthStatus.unauthenticated));
  }

  Future<void> _onRefresh(
    AuthTokenRefreshRequested event,
    Emitter<AuthState> emit,
  ) async {
    final refresh = await _storage.readRefreshToken();
    if (refresh == null || refresh.isEmpty) {
      emit(const AuthState(status: AuthStatus.unauthenticated));
      return;
    }
    try {
      await _repository.refresh(refresh);
      final user = await _repository.me();
      emit(state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
      ));
    } catch (_) {
      await _storage.clear();
      emit(const AuthState(status: AuthStatus.unauthenticated));
    }
  }

  String _humanize(Object error) {
    final s = error.toString();
    if (s.contains('401') || s.toLowerCase().contains('unauthorized')) {
      return 'Invalid email or password';
    }
    if (s.toLowerCase().contains('socket') ||
        s.toLowerCase().contains('connection')) {
      return 'Cannot reach the server. Check your network.';
    }
    return 'Something went wrong. Please try again.';
  }
}
