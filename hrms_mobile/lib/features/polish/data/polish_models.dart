import 'package:equatable/equatable.dart';

class Asset extends Equatable {
  const Asset({
    required this.id,
    required this.assetTag,
    required this.name,
    required this.category,
    required this.condition,
    required this.status,
    this.serialNumber,
    this.assignedTo,
    this.assignedAt,
  });

  final int id;
  final String assetTag;
  final String name;
  final String category;
  final String? serialNumber;
  final String condition;
  final String status;
  final int? assignedTo;
  final String? assignedAt;

  factory Asset.fromJson(Map<String, dynamic> j) => Asset(
        id: j['id'] as int,
        assetTag: j['asset_tag'] as String,
        name: j['name'] as String,
        category: j['category'] as String,
        serialNumber: j['serial_number'] as String?,
        condition: j['condition'] as String,
        status: j['status'] as String,
        assignedTo: j['assigned_to'] as int?,
        assignedAt: j['assigned_at'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}

class MeetingRoom extends Equatable {
  const MeetingRoom({
    required this.id,
    required this.code,
    required this.name,
    required this.capacity,
    required this.hasVideo,
    this.location,
  });

  final int id;
  final String code;
  final String name;
  final String? location;
  final int capacity;
  final bool hasVideo;

  factory MeetingRoom.fromJson(Map<String, dynamic> j) => MeetingRoom(
        id: j['id'] as int,
        code: j['code'] as String,
        name: j['name'] as String,
        location: j['location'] as String?,
        capacity: (j['capacity'] as int?) ?? 0,
        hasVideo: (j['has_video'] as bool?) ?? false,
      );

  @override
  List<Object?> get props => [id];
}

class RoomBooking extends Equatable {
  const RoomBooking({
    required this.id,
    required this.roomId,
    required this.title,
    required this.startTime,
    required this.endTime,
    required this.status,
  });

  final int id;
  final int roomId;
  final String title;
  final String startTime;
  final String endTime;
  final String status;

  factory RoomBooking.fromJson(Map<String, dynamic> j) => RoomBooking(
        id: j['id'] as int,
        roomId: j['room_id'] as int,
        title: j['title'] as String,
        startTime: j['start_time'] as String,
        endTime: j['end_time'] as String,
        status: j['status'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}

class JobPosting extends Equatable {
  const JobPosting({
    required this.id,
    required this.code,
    required this.title,
    required this.employmentType,
    required this.status,
    this.location,
    this.description,
    this.referralBonus,
  });

  final int id;
  final String code;
  final String title;
  final String employmentType;
  final String? location;
  final String? description;
  final double? referralBonus;
  final String status;

  factory JobPosting.fromJson(Map<String, dynamic> j) => JobPosting(
        id: j['id'] as int,
        code: j['code'] as String,
        title: j['title'] as String,
        employmentType: j['employment_type'] as String,
        location: j['location'] as String?,
        description: j['description'] as String?,
        referralBonus: j['referral_bonus'] != null
            ? double.tryParse(j['referral_bonus'].toString())
            : null,
        status: j['status'] as String,
      );

  @override
  List<Object?> get props => [id];
}

class JobApplication extends Equatable {
  const JobApplication({
    required this.id,
    required this.postingId,
    required this.status,
    required this.submittedAt,
  });

  final int id;
  final int postingId;
  final String status;
  final String submittedAt;

  factory JobApplication.fromJson(Map<String, dynamic> j) => JobApplication(
        id: j['id'] as int,
        postingId: j['posting_id'] as int,
        status: j['status'] as String,
        submittedAt: j['submitted_at'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}
