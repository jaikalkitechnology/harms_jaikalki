import 'package:equatable/equatable.dart';

class AttendanceRecord extends Equatable {
  const AttendanceRecord({
    required this.id,
    required this.date,
    this.checkIn,
    this.checkOut,
    this.checkInDistanceM,
    required this.status,
    required this.workMode,
    required this.totalMinutes,
    this.selfieUrl,
  });

  final int id;
  final String date;
  final String? checkIn;
  final String? checkOut;
  final int? checkInDistanceM;
  final String status;
  final String workMode;
  final int totalMinutes;
  final String? selfieUrl;

  factory AttendanceRecord.fromJson(Map<String, dynamic> json) =>
      AttendanceRecord(
        id: json['id'] as int,
        date: json['date'] as String,
        checkIn: json['check_in'] as String?,
        checkOut: json['check_out'] as String?,
        checkInDistanceM: json['check_in_distance_m'] as int?,
        status: (json['status'] as String?) ?? 'absent',
        workMode: (json['work_mode'] as String?) ?? 'office',
        totalMinutes: (json['total_minutes'] as int?) ?? 0,
        selfieUrl: json['check_in_selfie_url'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}
