import 'dart:convert';

import 'package:dio/dio.dart';

import '../../../core/storage/secure_storage.dart';
import 'dashboard_models.dart';

class DashboardApi {
  DashboardApi(this._dio, this._storage);
  final Dio _dio;
  final SecureStorage _storage;

  /// Fetch the dashboard. With [userId], the response is also saved so
  /// the next app start can show it instantly (see [cached]).
  Future<DashboardSummary> me({int? userId}) async {
    final res = await _dio.get<Map<String, dynamic>>('/api/v1/dashboard/me');
    final data = res.data!;
    if (userId != null) {
      try {
        await _storage.writeCache(
          _cacheName(userId),
          jsonEncode({'saved_on': _today(), 'data': data}),
        );
      } catch (_) {
        // The cache is best-effort.
      }
    }
    return DashboardSummary.fromJson(data);
  }

  /// The last dashboard saved for [userId], or null. Kept in secure
  /// storage, so a full sign-out removes it with the tokens. From an
  /// earlier day, today's attendance is dropped — a new day starts
  /// unchecked-in, and yesterday's check-in would mislead.
  Future<DashboardSummary?> cached(int userId) async {
    final raw = await _storage.readCache(_cacheName(userId));
    if (raw == null || raw.isEmpty) return null;
    try {
      final saved = jsonDecode(raw) as Map<String, dynamic>;
      final data = Map<String, dynamic>.from(saved['data'] as Map);
      if (saved['saved_on'] != _today()) {
        data['today_attendance'] = const <String, dynamic>{};
      }
      return DashboardSummary.fromJson(data);
    } catch (_) {
      return null;
    }
  }

  static String _cacheName(int userId) => 'dashboard.$userId';

  static String _today() {
    final d = DateTime.now();
    return '${d.year}-${d.month}-${d.day}';
  }
}
