import 'package:equatable/equatable.dart';

class Trainer extends Equatable {
  const Trainer({
    required this.id,
    required this.fullName,
    required this.isExternal,
    required this.yearsExperience,
    required this.ratingAverage,
    required this.sessionsCompleted,
    this.headline,
    this.bio,
    this.languages,
    this.specializations,
    this.profilePhotoUrl,
  });

  final int id;
  final String fullName;
  final bool isExternal;
  final String? headline;
  final String? bio;
  final List<String>? languages;
  final List<String>? specializations;
  final int yearsExperience;
  final double ratingAverage;
  final int sessionsCompleted;
  final String? profilePhotoUrl;

  factory Trainer.fromJson(Map<String, dynamic> j) => Trainer(
        id: j['id'] as int,
        fullName: j['full_name'] as String,
        isExternal: (j['is_external'] as bool?) ?? false,
        headline: j['headline'] as String?,
        bio: j['bio'] as String?,
        languages: (j['languages'] as List?)?.map((e) => e.toString()).toList(),
        specializations:
            (j['specializations'] as List?)?.map((e) => e.toString()).toList(),
        yearsExperience: (j['years_experience'] as int?) ?? 0,
        ratingAverage:
            double.tryParse(j['rating_average'].toString()) ?? 0,
        sessionsCompleted: (j['sessions_completed'] as int?) ?? 0,
        profilePhotoUrl: j['profile_photo_url'] as String?,
      );

  @override
  List<Object?> get props => [id];
}

class TrainingSession extends Equatable {
  const TrainingSession({
    required this.id,
    required this.code,
    required this.title,
    required this.trainerId,
    required this.sessionType,
    required this.scheduledStart,
    required this.scheduledEnd,
    required this.capacity,
    required this.participantsCount,
    required this.status,
    this.description,
    this.location,
    this.meetingUrl,
    this.qrToken,
    this.recordingUrl,
  });

  final int id;
  final String code;
  final String title;
  final String? description;
  final int trainerId;
  final String sessionType;
  final String scheduledStart;
  final String scheduledEnd;
  final String? location;
  final String? meetingUrl;
  final int capacity;
  final int participantsCount;
  final String? qrToken;
  final String? recordingUrl;
  final String status;

  factory TrainingSession.fromJson(Map<String, dynamic> j) => TrainingSession(
        id: j['id'] as int,
        code: j['code'] as String,
        title: j['title'] as String,
        description: j['description'] as String?,
        trainerId: j['trainer_id'] as int,
        sessionType: j['session_type'] as String,
        scheduledStart: j['scheduled_start'] as String,
        scheduledEnd: j['scheduled_end'] as String,
        location: j['location'] as String?,
        meetingUrl: j['meeting_url'] as String?,
        capacity: (j['capacity'] as int?) ?? 0,
        participantsCount: (j['participants_count'] as int?) ?? 0,
        qrToken: j['qr_token'] as String?,
        recordingUrl: j['recording_url'] as String?,
        status: j['status'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}

class Participant extends Equatable {
  const Participant({
    required this.id,
    required this.sessionId,
    required this.employeeId,
    required this.status,
    this.checkedInAt,
  });

  final int id;
  final int sessionId;
  final int employeeId;
  final String status;
  final String? checkedInAt;

  factory Participant.fromJson(Map<String, dynamic> j) => Participant(
        id: j['id'] as int,
        sessionId: j['session_id'] as int,
        employeeId: j['employee_id'] as int,
        status: j['status'] as String,
        checkedInAt: j['checked_in_at'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}
