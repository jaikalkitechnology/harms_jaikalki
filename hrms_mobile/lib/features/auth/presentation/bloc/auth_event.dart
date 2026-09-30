part of 'auth_bloc.dart';

abstract class AuthEvent extends Equatable {
  const AuthEvent();
  @override
  List<Object?> get props => [];
}

class AuthCheckRequested extends AuthEvent {
  const AuthCheckRequested();
}

class AuthLoginRequested extends AuthEvent {
  const AuthLoginRequested({
    required this.email,
    required this.password,
    this.rememberMe = false,
  });

  final String email;
  final String password;
  final bool rememberMe;

  @override
  List<Object?> get props => [email, password, rememberMe];
}

class AuthBiometricLoginRequested extends AuthEvent {
  const AuthBiometricLoginRequested();
}

/// Opt in/out of biometric sign-in. Enabling runs a one-time biometric
/// prompt to confirm the user can authenticate before storing the flag.
class AuthBiometricToggleRequested extends AuthEvent {
  const AuthBiometricToggleRequested(this.enable);
  final bool enable;

  @override
  List<Object?> get props => [enable];
}

class AuthLogoutRequested extends AuthEvent {
  const AuthLogoutRequested();
}

class AuthTokenRefreshRequested extends AuthEvent {
  const AuthTokenRefreshRequested();
}

/// The server rejected the refresh token mid-session (logged out on
/// another device, password changed, revoked).
class AuthSessionExpired extends AuthEvent {
  const AuthSessionExpired();
}
