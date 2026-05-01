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

class AuthLogoutRequested extends AuthEvent {
  const AuthLogoutRequested();
}

class AuthTokenRefreshRequested extends AuthEvent {
  const AuthTokenRefreshRequested();
}
