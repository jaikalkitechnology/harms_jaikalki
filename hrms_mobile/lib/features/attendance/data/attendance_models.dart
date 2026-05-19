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

class CalendarDay extends Equatable {
  const CalendarDay({
    required this.date,
    required this.weekday,
    required this.status,
    required this.isSunday,
    required this.isHoliday,
    this.holidayName,
    required this.isEditable,
    this.checkIn,
    this.checkOut,
    this.workMode,
    this.totalMinutes = 0,
    this.notes,
    this.leaveType,
    this.isLate = false,
    this.lateRemark,
  });

  final String date;       // YYYY-MM-DD
  final int weekday;       // 0 Mon — 6 Sun
  final String status;
  final bool isSunday;
  final bool isHoliday;
  final String? holidayName;
  final bool isEditable;
  final String? checkIn;
  final String? checkOut;
  final String? workMode;
  final int totalMinutes;
  final String? notes;
  final String? leaveType;
  final bool isLate;
  final String? lateRemark;

  factory CalendarDay.fromJson(Map<String, dynamic> j) => CalendarDay(
        date: j['date'] as String,
        weekday: (j['weekday'] as int?) ?? 0,
        status: (j['status'] as String?) ?? 'absent',
        isSunday: j['is_sunday'] as bool? ?? false,
        isHoliday: j['is_holiday'] as bool? ?? false,
        holidayName: j['holiday_name'] as String?,
        isEditable: j['is_editable'] as bool? ?? true,
        checkIn: j['check_in'] as String?,
        checkOut: j['check_out'] as String?,
        workMode: j['work_mode'] as String?,
        totalMinutes: (j['total_minutes'] as int?) ?? 0,
        notes: j['notes'] as String?,
        leaveType: j['leave_type'] as String?,
        isLate: j['is_late'] as bool? ?? false,
        lateRemark: j['late_remark'] as String?,
      );

  @override
  List<Object?> get props =>
      [date, status, isHoliday, isSunday, isLate];
}

class AttendanceCalendar extends Equatable {
  const AttendanceCalendar({
    required this.year,
    required this.month,
    required this.days,
    required this.daysPresent,
    required this.daysAbsent,
    required this.daysLeave,
    required this.daysHoliday,
    required this.daysWeekoff,
    required this.daysHalfDay,
    required this.daysWfh,
    required this.workingDays,
  });

  final int year;
  final int month;
  final List<CalendarDay> days;
  final int daysPresent;
  final int daysAbsent;
  final int daysLeave;
  final int daysHoliday;
  final int daysWeekoff;
  final int daysHalfDay;
  final int daysWfh;
  final int workingDays;

  factory AttendanceCalendar.fromJson(Map<String, dynamic> j) =>
      AttendanceCalendar(
        year: j['year'] as int,
        month: j['month'] as int,
        days: ((j['days'] as List?) ?? const [])
            .map((d) => CalendarDay.fromJson(d as Map<String, dynamic>))
            .toList(),
        daysPresent: (j['days_present'] as int?) ?? 0,
        daysAbsent: (j['days_absent'] as int?) ?? 0,
        daysLeave: (j['days_leave'] as int?) ?? 0,
        daysHoliday: (j['days_holiday'] as int?) ?? 0,
        daysWeekoff: (j['days_weekoff'] as int?) ?? 0,
        daysHalfDay: (j['days_half_day'] as int?) ?? 0,
        daysWfh: (j['days_wfh'] as int?) ?? 0,
        workingDays: (j['working_days'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [year, month, days];
}
