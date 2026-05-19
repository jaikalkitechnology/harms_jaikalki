part of 'auth_bloc.dart';

enum AuthStatus { initial, loading, authenticated, unauthenticated, error }

class AuthState extends Equatable {
  const AuthState({
    required this.status,
    this.user,
    this.errorMessage,
    this.biometricEnabled = false,
    this.biometricAvailable = false,
  });

  const AuthState.initial()
      : status = AuthStatus.initial,
        user = null,
        errorMessage = null,
        biometricEnabled = false,
        biometricAvailable = false;

  final AuthStatus status;
  final AuthUser? user;
  final String? errorMessage;

  /// User opted in to biometric sign-in and a session token is stored.
  final bool biometricEnabled;

  /// Device hardware can do biometric / device-credential auth.
  final bool biometricAvailable;

  bool get isAuthenticated =>
      status == AuthStatus.authenticated && user != null;

  /// Only surface the biometric button when it can actually work.
  bool get canUseBiometric => biometricEnabled && biometricAvailable;

  AuthState copyWith({
    AuthStatus? status,
    AuthUser? user,
    String? errorMessage,
    bool? biometricEnabled,
    bool? biometricAvailable,
    bool clearError = false,
    bool clearUser = false,
  }) =>
      AuthState(
        status: status ?? this.status,
        user: clearUser ? null : (user ?? this.user),
        errorMessage:
            clearError ? null : (errorMessage ?? this.errorMessage),
        biometricEnabled: biometricEnabled ?? this.biometricEnabled,
        biometricAvailable:
            biometricAvailable ?? this.biometricAvailable,
      );

  @override
  List<Object?> get props =>
      [status, user, errorMessage, biometricEnabled, biometricAvailable];
}
