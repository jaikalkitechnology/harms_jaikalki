import 'package:dio/dio.dart';
import 'package:equatable/equatable.dart';

class NotificationItem extends Equatable {
  const NotificationItem({
    required this.id,
    required this.type,
    required this.title,
    required this.status,
    required this.createdAt,
    this.body,
    this.readAt,
  });

  final int id;
  final String type;
  final String title;
  final String? body;
  final String status;
  final String? readAt;
  final String createdAt;

  bool get isRead => readAt != null;

  factory NotificationItem.fromJson(Map<String, dynamic> j) =>
      NotificationItem(
        id: j['id'] as int,
        type: j['type'] as String,
        title: j['title'] as String,
        body: j['body'] as String?,
        status: j['status'] as String,
        readAt: j['read_at'] as String?,
        createdAt: j['created_at'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}

class MfaEnrollResponse extends Equatable {
  const MfaEnrollResponse({required this.secret, required this.otpauthUri});
  final String secret;
  final String otpauthUri;

  factory MfaEnrollResponse.fromJson(Map<String, dynamic> j) =>
      MfaEnrollResponse(
        secret: j['secret'] as String,
        otpauthUri: j['otpauth_uri'] as String,
      );

  @override
  List<Object?> get props => [secret];
}


class LaunchApi {
  LaunchApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  // ── Notifications ─────────────────────────────────────────────
  Future<List<NotificationItem>> myNotifications() async {
    final res = await _dio.get<List<dynamic>>('$_v1/notifications/me');
    return (res.data ?? const [])
        .map((e) => NotificationItem.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<int> unreadCount() async {
    final res = await _dio
        .get<Map<String, dynamic>>('$_v1/notifications/me/unread-count');
    return (res.data?['unread'] as int?) ?? 0;
  }

  Future<NotificationItem> markRead(int id) async {
    final res = await _dio
        .post<Map<String, dynamic>>('$_v1/notifications/$id/read');
    return NotificationItem.fromJson(res.data!);
  }

  Future<int> markAllRead() async {
    final res = await _dio
        .post<Map<String, dynamic>>('$_v1/notifications/me/read-all');
    return (res.data?['marked'] as int?) ?? 0;
  }

  Future<void> registerDeviceToken({
    required String platform,
    required String token,
  }) async {
    await _dio.post(
      '$_v1/notifications/devices',
      data: {'platform': platform, 'token': token},
    );
  }

  // ── Forgot password ───────────────────────────────────────────
  Future<void> requestPasswordOtp(String email) async {
    await _dio.post(
      '$_v1/auth/forgot-password',
      data: {'email': email},
    );
  }

  Future<void> resetPassword({
    required String email,
    required String otp,
    required String newPassword,
  }) async {
    await _dio.post(
      '$_v1/auth/reset-password',
      data: {
        'email': email,
        'otp': otp,
        'new_password': newPassword,
      },
    );
  }

  // ── MFA ───────────────────────────────────────────────────────
  Future<MfaEnrollResponse> mfaEnroll() async {
    final res = await _dio.post<Map<String, dynamic>>('$_v1/auth/mfa/enroll');
    return MfaEnrollResponse.fromJson(res.data!);
  }

  Future<List<String>> mfaVerify(String code) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/auth/mfa/verify',
      data: {'code': code},
    );
    return ((res.data?['backup_codes'] as List?) ?? const [])
        .map((e) => e.toString())
        .toList();
  }

  Future<void> mfaDisable(String code) async {
    await _dio.post('$_v1/auth/mfa/disable', data: {'code': code});
  }

  // ── Resignation ───────────────────────────────────────────────
  Future<void> submitResignation({
    required String proposedLastWorkingDay,
    String? reason,
    int noticePeriodDays = 60,
  }) async {
    await _dio.post(
      '$_v1/resignations',
      data: {
        'proposed_last_working_day': proposedLastWorkingDay,
        if (reason != null) 'reason': reason,
        'notice_period_days': noticePeriodDays,
      },
    );
  }

  Future<List<dynamic>> myResignations() async {
    final res = await _dio.get<List<dynamic>>('$_v1/resignations/me');
    return res.data ?? const [];
  }

  /// Returns {unlocked: bool, has_open_request: bool}.
  Future<Map<String, dynamic>> resignationUnlockStatus() async {
    final res = await _dio.get<Map<String, dynamic>>(
      '$_v1/resignations/me/unlock-status',
    );
    return res.data ?? const {};
  }
}
