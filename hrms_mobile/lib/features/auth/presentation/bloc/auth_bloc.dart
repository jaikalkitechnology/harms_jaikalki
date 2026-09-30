import 'dart:async';

import 'package:bloc/bloc.dart';
import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';
import 'package:local_auth/local_auth.dart';

import '../../../../core/di/injection.dart';
import '../../../../core/network/session_events.dart';
import '../../../../core/push/push_notifications_service.dart';
import '../../../../core/storage/secure_storage.dart';
import '../../../launch/data/launch_api.dart';
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
    on<AuthBiometricToggleRequested>(_onBiometricToggle);
    on<AuthLogoutRequested>(_onLogout);
    on<AuthTokenRefreshRequested>(_onRefresh);
    on<AuthSessionExpired>(_onSessionExpired);
    _expiredSub =
        SessionEvents.expired.listen((_) => add(const AuthSessionExpired()));
  }

  final AuthRepository _repository;
  final SecureStorage _storage;
  final LocalAuthentication _localAuth;
  late final StreamSubscription<void> _expiredSub;

  @override
  Future<void> close() {
    _expiredSub.cancel();
    return super.close();
  }

  /// The server said the session is invalid — as opposed to the request
  /// not getting through (offline, timeout, server down).
  static bool _isAuthFailure(Object e) {
    if (e is! DioException) return false;
    final code = e.response?.statusCode;
    return code == 401 || code == 403;
  }

  /// Device can do biometric OR device-credential (PIN/pattern) auth.
  Future<bool> _deviceCanAuth() async {
    try {
      return (await _localAuth.isDeviceSupported()) ||
          (await _localAuth.canCheckBiometrics);
    } catch (_) {
      return false;
    }
  }

  Future<void> _onCheck(
    AuthCheckRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(state.copyWith(status: AuthStatus.loading, clearError: true));
    final access = await _storage.readAccessToken();
    final refresh = await _storage.readRefreshToken();
    final hasAccess = access != null && access.isNotEmpty;
    final hasRefresh = refresh != null && refresh.isNotEmpty;
    final bioEnabled = await _storage.isBiometricEnabled();

    if (!hasAccess && !hasRefresh) {
      emit(state.copyWith(
        status: AuthStatus.unauthenticated,
        clearUser: true,
        biometricEnabled: false,
        biometricAvailable: false,
      ));
      return;
    }

    if (!hasAccess && bioEnabled) {
      // Soft-signed-out with biometric on: the refresh token is kept
      // behind the fingerprint / face prompt on the login screen.
      final canBio = await _deviceCanAuth();
      emit(state.copyWith(
        status: AuthStatus.unauthenticated,
        clearUser: true,
        biometricEnabled: canBio,
        biometricAvailable: canBio,
      ));
      return;
    }

    try {
      // Only a refresh token left (access token lost) — mint a new pair.
      // An expired access token is refreshed by the interceptor.
      if (!hasAccess) await _repository.refresh(refresh!);
      final user = await _repository.me();
      emit(state.copyWith(
        status: AuthStatus.authenticated,
        user: user,
        biometricEnabled: bioEnabled,
        biometricAvailable: await _deviceCanAuth(),
      ));
      _registerPushToken();
    } catch (e) {
      if (_isAuthFailure(e)) {
        await _storage.clear();
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          clearUser: true,
          biometricEnabled: false,
        ));
        return;
      }
      // Offline or server unreachable: keep the session and open with
      // the last known user. Requests recover once the network is back.
      final cached = await _repository.cachedUser();
      if (cached != null) {
        emit(state.copyWith(
          status: AuthStatus.authenticated,
          user: cached,
          biometricEnabled: bioEnabled,
          biometricAvailable: await _deviceCanAuth(),
        ));
        return;
      }
      emit(state.copyWith(
        status: AuthStatus.unauthenticated,
        clearUser: true,
        errorMessage: 'Cannot reach the server. Check your network.',
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
        biometricEnabled: await _storage.isBiometricEnabled(),
        biometricAvailable: await _deviceCanAuth(),
      ));
      _registerPushToken();
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
      if (!await _storage.isBiometricEnabled()) {
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          errorMessage:
              'Biometric sign-in is off. Sign in with your password, '
              'then enable it in Settings.',
        ));
        return;
      }
      final refresh = await _storage.readRefreshToken();
      if (refresh == null || refresh.isEmpty) {
        await _storage.setBiometricEnabled(false);
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          errorMessage:
              'Saved session expired. Please sign in with your password.',
          biometricEnabled: false,
        ));
        return;
      }
      if (!await _deviceCanAuth()) {
        emit(state.copyWith(
          status: AuthStatus.error,
          errorMessage: 'Biometrics not available on this device',
        ));
        return;
      }

      final ok = await _localAuth.authenticate(
        localizedReason: 'Sign in to Jaikalki HRMS',
        options: const AuthenticationOptions(
          // biometricOnly:false lets a failed scan fall back to the
          // device PIN/pattern — far more reliable in the field.
          biometricOnly: false,
          stickyAuth: true,
        ),
      );
      if (!ok) {
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          errorMessage: 'Biometric authentication cancelled',
        ));
        return;
      }

      emit(state.copyWith(status: AuthStatus.loading, clearError: true));
      // Try the stored access token first; fall back to a refresh.
      try {
        final user = await _repository.me();
        emit(state.copyWith(
          status: AuthStatus.authenticated,
          user: user,
          biometricEnabled: true,
          biometricAvailable: true,
        ));
        _registerPushToken();
        return;
      } catch (_) {
        // access token likely expired — refresh below.
      }
      try {
        await _repository.refresh(refresh);
        final user = await _repository.me();
        emit(state.copyWith(
          status: AuthStatus.authenticated,
          user: user,
          biometricEnabled: true,
          biometricAvailable: true,
        ));
        _registerPushToken();
      } catch (e) {
        if (!_isAuthFailure(e)) {
          emit(state.copyWith(
            status: AuthStatus.unauthenticated,
            errorMessage: 'Cannot reach the server. Check your network.',
          ));
          return;
        }
        await _storage.clear();
        emit(state.copyWith(
          status: AuthStatus.unauthenticated,
          errorMessage:
              'Saved session expired. Please sign in with your password.',
          biometricEnabled: false,
          clearUser: true,
        ));
      }
    } catch (e) {
      emit(state.copyWith(
        status: AuthStatus.error,
        errorMessage: _humanize(e),
      ));
    }
  }

  Future<void> _onBiometricToggle(
    AuthBiometricToggleRequested event,
    Emitter<AuthState> emit,
  ) async {
    if (!event.enable) {
      await _storage.setBiometricEnabled(false);
      emit(state.copyWith(biometricEnabled: false));
      return;
    }
    // Can only enable while signed in with a refreshable session.
    final refresh = await _storage.readRefreshToken();
    if (refresh == null || refresh.isEmpty) {
      emit(state.copyWith(
        errorMessage:
            'Sign in with your password first, then enable biometrics.',
      ));
      return;
    }
    if (!await _deviceCanAuth()) {
      emit(state.copyWith(
        errorMessage:
            'This device has no biometrics or screen lock set up.',
      ));
      return;
    }
    try {
      final ok = await _localAuth.authenticate(
        localizedReason: 'Confirm to enable biometric sign-in',
        options: const AuthenticationOptions(
          biometricOnly: false,
          stickyAuth: true,
        ),
      );
      if (!ok) {
        emit(state.copyWith(biometricEnabled: false));
        return;
      }
      await _storage.setBiometricEnabled(true);
      emit(state.copyWith(
        biometricEnabled: true,
        biometricAvailable: true,
      ));
    } catch (e) {
      emit(state.copyWith(errorMessage: _humanize(e)));
    }
  }

  Future<void> _onLogout(
    AuthLogoutRequested event,
    Emitter<AuthState> emit,
  ) async {
    // Best-effort: drop the FCM token before we tear down the session,
    // otherwise the server keeps sending pushes to a dead session.
    if (sl.isRegistered<LaunchApi>()) {
      await PushNotificationsService.instance.unregisterToken(sl<LaunchApi>());
    }

    if (await _storage.isBiometricEnabled()) {
      // Soft sign-out: keep the biometric-protected refresh token so
      // the user can re-enter with fingerprint/Face ID. Only the
      // access token is dropped; the server refresh stays valid.
      await _storage.clearAccessToken();
      final canBio = await _deviceCanAuth();
      emit(AuthState(
        status: AuthStatus.unauthenticated,
        biometricEnabled: true,
        biometricAvailable: canBio,
      ));
      return;
    }

    // Full sign-out: revoke + wipe everything.
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
      _registerPushToken();
    } catch (e) {
      // A network failure leaves the current session as it is.
      if (!_isAuthFailure(e)) return;
      await _storage.clear();
      emit(const AuthState(status: AuthStatus.unauthenticated));
    }
  }

  Future<void> _onSessionExpired(
    AuthSessionExpired event,
    Emitter<AuthState> emit,
  ) async {
    if (!state.isAuthenticated) return;
    emit(const AuthState(
      status: AuthStatus.unauthenticated,
      errorMessage: 'Your session has ended. Please sign in again.',
    ));
  }

  /// Fire-and-forget — never blocks the UI on a token registration.
  void _registerPushToken() {
    if (!sl.isRegistered<LaunchApi>()) return;
    PushNotificationsService.instance.registerToken(sl<LaunchApi>());
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
