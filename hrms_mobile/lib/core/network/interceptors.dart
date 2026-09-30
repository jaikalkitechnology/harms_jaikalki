import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../constants/app_constants.dart';
import '../di/injection.dart';
import '../storage/secure_storage.dart';
import 'session_events.dart';

class AuthInterceptor extends Interceptor {
  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    // Skip token attachment for the auth endpoints themselves.
    final path = options.path;
    final isAuthEndpoint = path.contains('/auth/login') ||
        path.contains('/auth/refresh') ||
        path.contains('/auth/logout');

    if (!isAuthEndpoint) {
      final storage = sl<SecureStorage>();
      final token = await storage.readAccessToken();
      if (token != null && token.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $token';
      }
    }
    handler.next(options);
  }
}

/// Handles 401 by transparently refreshing the access token and retrying once.
///
/// Queued, so concurrent 401s are handled one after another: the first
/// refreshes, the rest see the new token and just retry. The stored
/// session is only dropped when the server rejects the refresh token
/// itself — a timeout or dropped connection during refresh keeps the
/// user signed in so the next request can try again.
class RefreshInterceptor extends QueuedInterceptor {
  RefreshInterceptor();

  static const _retriedKey = '_auth_retried';

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final options = err.requestOptions;
    final isUnauthorized = err.response?.statusCode == 401;
    final path = options.path;
    final isAuthCall = path.contains('/auth/refresh') ||
        path.contains('/auth/login') ||
        path.contains('/auth/logout');

    if (!isUnauthorized || isAuthCall || options.extra[_retriedKey] == true) {
      return handler.next(err);
    }

    final storage = sl<SecureStorage>();
    final sentToken = _bearer(options.headers['Authorization']);
    final storedAccess = await storage.readAccessToken();

    // Another queued request already refreshed — retry with the new token.
    if (storedAccess != null &&
        storedAccess.isNotEmpty &&
        storedAccess != sentToken) {
      return _retry(options, storedAccess, handler, err);
    }

    final refresh = await storage.readRefreshToken();
    if (refresh == null || refresh.isEmpty) {
      return handler.next(err);
    }

    final String newAccess;
    try {
      // Bare Dio so this call doesn't recurse through our interceptors.
      final bareDio = Dio(
        BaseOptions(
          baseUrl: AppConstants.apiBaseUrl,
          connectTimeout: AppConstants.networkTimeout,
          receiveTimeout: AppConstants.networkTimeout,
        ),
      );
      final res = await bareDio.post<Map<String, dynamic>>(
        '/api/v1/auth/refresh',
        data: {'refresh_token': refresh},
      );
      final data = res.data!;
      newAccess = data['access_token'] as String;
      await storage.writeAccessToken(newAccess);
      await storage.writeRefreshToken(data['refresh_token'] as String);
    } on DioException catch (e) {
      if (isRejectedRefresh(e)) {
        // The session is really over (logged out, revoked, expired).
        await storage.clear();
        SessionEvents.notifyExpired();
        return handler.next(err);
      }
      // Couldn't reach the server: report that, not the 401, so callers
      // don't treat a network blip as a logout.
      return handler.next(e);
    } catch (_) {
      return handler.next(err);
    }

    return _retry(options, newAccess, handler, err);
  }

  Future<void> _retry(
    RequestOptions options,
    String accessToken,
    ErrorInterceptorHandler handler,
    DioException original,
  ) async {
    final data = options.data;
    final retryOptions = options.copyWith(
      // A FormData body can only be sent once.
      data: data is FormData ? data.clone() : data,
      headers: {...options.headers, 'Authorization': 'Bearer $accessToken'},
      extra: {...options.extra, _retriedKey: true},
    );
    try {
      final response = await sl<Dio>().fetch<dynamic>(retryOptions);
      return handler.resolve(response);
    } on DioException catch (e) {
      return handler.next(e);
    } catch (_) {
      return handler.next(original);
    }
  }

  static String? _bearer(Object? header) {
    if (header is! String || !header.startsWith('Bearer ')) return null;
    return header.substring(7);
  }
}

/// True when the server refused the refresh token itself, as opposed to
/// the request failing to reach it.
bool isRejectedRefresh(DioException e) {
  final code = e.response?.statusCode;
  return code == 401 || code == 403 || code == 422;
}

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    if (kDebugMode) {
      debugPrint('→ ${options.method} ${options.uri}');
    }
    handler.next(options);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    if (kDebugMode) {
      debugPrint(
        '← ${response.statusCode} ${response.requestOptions.method} ${response.requestOptions.uri}',
      );
    }
    handler.next(response);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    if (kDebugMode) {
      debugPrint(
        '✖ ${err.response?.statusCode} ${err.requestOptions.uri}',
      );
    }
    handler.next(err);
  }
}
