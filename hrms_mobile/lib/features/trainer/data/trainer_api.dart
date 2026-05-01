import 'package:dio/dio.dart';

import 'trainer_models.dart';

class TrainerApi {
  TrainerApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<Trainer>> trainers({String? search, String? specialization}) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/trainer/trainers',
      queryParameters: {
        if (search != null) 'search': search,
        if (specialization != null) 'specialization': specialization,
      },
    );
    return (res.data ?? const [])
        .map((e) => Trainer.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<TrainingSession>> upcomingSessions() async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/trainer/sessions',
      queryParameters: {'upcoming_only': true},
    );
    return (res.data ?? const [])
        .map((e) => TrainingSession.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<TrainingSession>> mySessions() async {
    final res = await _dio.get<List<dynamic>>('$_v1/trainer/sessions/me');
    return (res.data ?? const [])
        .map((e) => TrainingSession.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Participant> register(int sessionId) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/trainer/sessions/$sessionId/register',
    );
    return Participant.fromJson(res.data!);
  }

  Future<Participant> checkIn(String qrToken) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/trainer/sessions/check-in',
      data: {'qr_token': qrToken},
    );
    return Participant.fromJson(res.data!);
  }

  Future<void> review({
    required int sessionId,
    required int rating,
    String? text,
    bool anonymous = false,
  }) async {
    await _dio.post(
      '$_v1/trainer/sessions/$sessionId/review',
      data: {
        'rating': rating,
        if (text != null) 'review_text': text,
        'is_anonymous': anonymous,
      },
    );
  }
}
