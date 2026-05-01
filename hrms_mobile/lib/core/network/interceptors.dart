import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';

import '../constants/app_constants.dart';
import '../di/injection.dart';
import '../storage/secure_storage.dart';

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
class RefreshInterceptor extends QueuedInterceptor {
  RefreshInterceptor();

  bool _refreshing = false;

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    final response = err.response;
    final isUnauthorized = response?.statusCode == 401;
    final isRefreshCall =
        err.requestOptions.path.contains('/auth/refresh');

    if (!isUnauthorized || isRefreshCall || _refreshing) {
      return handler.next(err);
    }

    _refreshing = true;
    try {
      final storage = sl<SecureStorage>();
      final refresh = await storage.readRefreshToken();
      if (refresh == null || refresh.isEmpty) {
        return handler.next(err);
      }

      // Use a bare Dio so this call doesn't recurse through our interceptors.
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
      await storage.writeAccessToken(data['access_token'] as String);
      await storage.writeRefreshToken(data['refresh_token'] as String);

      // Retry original request with new token.
      final retryOptions = Options(
        method: err.requestOptions.method,
        headers: {
          ...err.requestOptions.headers,
          'Authorization': 'Bearer ${data['access_token']}',
        },
      );
      final dio = sl<Dio>();
      final retried = await dio.request<dynamic>(
        err.requestOptions.path,
        data: err.requestOptions.data,
        queryParameters: err.requestOptions.queryParameters,
        options: retryOptions,
      );
      return handler.resolve(retried);
    } catch (_) {
      // Refresh failed — let the 401 propagate so the UI can route to login.
      await sl<SecureStorage>().clear();
      return handler.next(err);
    } finally {
      _refreshing = false;
    }
  }
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
