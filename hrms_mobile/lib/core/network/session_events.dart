import 'dart:async';

/// Signals from the network layer that the auth state must react to.
///
/// The refresh interceptor fires [notifyExpired] when the server rejects
/// the refresh token (logged out elsewhere, password changed, revoked).
/// AuthBloc listens and returns the user to the login screen.
class SessionEvents {
  SessionEvents._();

  static final _expired = StreamController<void>.broadcast();

  static Stream<void> get expired => _expired.stream;

  static void notifyExpired() => _expired.add(null);
}
