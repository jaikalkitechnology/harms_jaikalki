import 'package:bloc_test/bloc_test.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hrms_mobile/core/network/session_events.dart';
import 'package:hrms_mobile/core/storage/secure_storage.dart';
import 'package:hrms_mobile/features/auth/domain/entities/auth_user.dart';
import 'package:hrms_mobile/features/auth/domain/entities/token_pair.dart';
import 'package:hrms_mobile/features/auth/domain/repositories/auth_repository.dart';
import 'package:hrms_mobile/features/auth/presentation/bloc/auth_bloc.dart';
import 'package:local_auth/local_auth.dart';
import 'package:mocktail/mocktail.dart';

class _Repo extends Mock implements AuthRepository {}

class _Storage extends Mock implements SecureStorage {}

class _LocalAuth extends Mock implements LocalAuthentication {}

const _user = AuthUser(
  id: 1,
  email: 'e@jaikalki.com',
  fullName: 'Emp',
  isActive: true,
  role: 'employee',
  roleLevel: 10,
  roles: ['employee'],
  permissions: [],
);

DioException _status(int code) {
  final req = RequestOptions(path: '/api/v1/auth/me');
  return DioException(
    requestOptions: req,
    response: Response(requestOptions: req, statusCode: code),
    type: DioExceptionType.badResponse,
  );
}

DioException _offline() => DioException(
      requestOptions: RequestOptions(path: '/api/v1/auth/me'),
      type: DioExceptionType.connectionError,
    );

void main() {
  late _Repo repo;
  late _Storage storage;
  late _LocalAuth localAuth;

  AuthBloc build() =>
      AuthBloc(repository: repo, storage: storage, localAuth: localAuth);

  void tokens({String? access, String? refresh, bool bio = false}) {
    when(() => storage.readAccessToken()).thenAnswer((_) async => access);
    when(() => storage.readRefreshToken()).thenAnswer((_) async => refresh);
    when(() => storage.isBiometricEnabled()).thenAnswer((_) async => bio);
  }

  setUp(() {
    repo = _Repo();
    storage = _Storage();
    localAuth = _LocalAuth();
    when(() => localAuth.isDeviceSupported()).thenAnswer((_) async => false);
    when(() => localAuth.canCheckBiometrics).thenAnswer((_) async => false);
    when(() => storage.clear()).thenAnswer((_) async {});
  });

  group('start-up session check', () {
    blocTest<AuthBloc, AuthState>(
      'stays signed in with the cached user when the server is unreachable',
      build: build,
      setUp: () {
        tokens(access: 'a', refresh: 'r');
        when(() => repo.me()).thenThrow(_offline());
        when(() => repo.cachedUser()).thenAnswer((_) async => _user);
      },
      act: (b) => b.add(const AuthCheckRequested()),
      expect: () => [
        isA<AuthState>().having((s) => s.status, 'status', AuthStatus.loading),
        isA<AuthState>()
            .having((s) => s.status, 'status', AuthStatus.authenticated)
            .having((s) => s.user, 'user', _user),
      ],
      verify: (_) => verifyNever(() => storage.clear()),
    );

    blocTest<AuthBloc, AuthState>(
      'signs out only when the server rejects the session',
      build: build,
      setUp: () {
        tokens(access: 'a', refresh: 'r');
        when(() => repo.me()).thenThrow(_status(401));
      },
      act: (b) => b.add(const AuthCheckRequested()),
      expect: () => [
        isA<AuthState>().having((s) => s.status, 'status', AuthStatus.loading),
        isA<AuthState>()
            .having((s) => s.status, 'status', AuthStatus.unauthenticated),
      ],
      verify: (_) => verify(() => storage.clear()).called(1),
    );

    blocTest<AuthBloc, AuthState>(
      'uses the refresh token when the access token is missing',
      build: build,
      setUp: () {
        tokens(access: null, refresh: 'r');
        when(() => repo.refresh('r')).thenAnswer(
          (_) async => const TokenPair(
            accessToken: 'a2',
            refreshToken: 'r2',
            expiresIn: 900,
          ),
        );
        when(() => repo.me()).thenAnswer((_) async => _user);
      },
      act: (b) => b.add(const AuthCheckRequested()),
      expect: () => [
        isA<AuthState>().having((s) => s.status, 'status', AuthStatus.loading),
        isA<AuthState>()
            .having((s) => s.status, 'status', AuthStatus.authenticated),
      ],
      verify: (_) => verify(() => repo.refresh('r')).called(1),
    );

    blocTest<AuthBloc, AuthState>(
      'goes to login when nothing is stored',
      build: build,
      setUp: () => tokens(),
      act: (b) => b.add(const AuthCheckRequested()),
      expect: () => [
        isA<AuthState>().having((s) => s.status, 'status', AuthStatus.loading),
        isA<AuthState>()
            .having((s) => s.status, 'status', AuthStatus.unauthenticated),
      ],
      verify: (_) => verifyNever(() => repo.me()),
    );
  });

  blocTest<AuthBloc, AuthState>(
    'returns to login when the network layer reports the session expired',
    build: build,
    seed: () => const AuthState(status: AuthStatus.authenticated, user: _user),
    act: (_) async {
      SessionEvents.notifyExpired();
      await Future<void>.delayed(Duration.zero);
    },
    expect: () => [
      isA<AuthState>()
          .having((s) => s.status, 'status', AuthStatus.unauthenticated)
          .having((s) => s.errorMessage, 'message', isNotNull),
    ],
  );
}
