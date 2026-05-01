import 'package:dio/dio.dart';

import '../models/auth_response_model.dart';
import '../models/user_model.dart';

class AuthRemoteDataSource {
  AuthRemoteDataSource(this._dio);
  final Dio _dio;

  Future<AuthResponseModel> login({
    required String email,
    required String password,
    bool rememberMe = false,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/login',
      data: {
        'email': email,
        'password': password,
        'remember_me': rememberMe,
      },
    );
    return AuthResponseModel.fromJson(response.data!);
  }

  Future<AuthResponseModel> refresh(String refreshToken) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/v1/auth/refresh',
      data: {'refresh_token': refreshToken},
    );
    return AuthResponseModel.fromJson(response.data!);
  }

  Future<void> logout(String refreshToken) async {
    await _dio.post<void>(
      '/api/v1/auth/logout',
      data: {'refresh_token': refreshToken},
    );
  }

  Future<MeResponseModel> me() async {
    final response = await _dio.get<Map<String, dynamic>>('/api/v1/auth/me');
    return MeResponseModel.fromJson(response.data!);
  }

  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    await _dio.post<void>(
      '/api/v1/auth/change-password',
      data: {
        'old_password': oldPassword,
        'new_password': newPassword,
      },
    );
  }
}
