import 'package:dio/dio.dart';

import '../constants/app_constants.dart';
import 'interceptors.dart';

class DioClient {
  DioClient._();

  static Dio create() {
    final dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: AppConstants.networkTimeout,
        receiveTimeout: AppConstants.networkTimeout,
        contentType: 'application/json',
        responseType: ResponseType.json,
      ),
    );
    dio.interceptors.addAll([
      AuthInterceptor(),
      LoggingInterceptor(),
    ]);
    return dio;
  }
}
