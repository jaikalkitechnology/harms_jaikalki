import 'package:equatable/equatable.dart';

class Customer extends Equatable {
  const Customer({
    required this.id,
    required this.name,
    required this.type,
    this.address,
    this.city,
    this.geoLat,
    this.geoLng,
    this.territory,
  });

  final int id;
  final String name;
  final String type;
  final String? address;
  final String? city;
  final double? geoLat;
  final double? geoLng;
  final String? territory;

  factory Customer.fromJson(Map<String, dynamic> j) => Customer(
        id: j['id'] as int,
        name: j['name'] as String,
        type: j['type'] as String,
        address: j['address'] as String?,
        city: j['city'] as String?,
        geoLat: j['geo_lat'] != null
            ? double.tryParse(j['geo_lat'].toString())
            : null,
        geoLng: j['geo_lng'] != null
            ? double.tryParse(j['geo_lng'].toString())
            : null,
        territory: j['territory'] as String?,
      );

  @override
  List<Object?> get props => [id];
}

class FieldJob extends Equatable {
  const FieldJob({
    required this.id,
    required this.employeeId,
    required this.customerId,
    required this.jobType,
    required this.scheduledDate,
    required this.priority,
    required this.status,
    this.scheduledTime,
    this.notes,
    this.customer,
  });

  final int id;
  final int employeeId;
  final int customerId;
  final String jobType;
  final String scheduledDate;
  final String? scheduledTime;
  final String priority;
  final String status;
  final String? notes;
  final Customer? customer;

  factory FieldJob.fromJson(Map<String, dynamic> j) => FieldJob(
        id: j['id'] as int,
        employeeId: j['employee_id'] as int,
        customerId: j['customer_id'] as int,
        jobType: j['job_type'] as String,
        scheduledDate: j['scheduled_date'] as String,
        scheduledTime: j['scheduled_time'] as String?,
        priority: j['priority'] as String,
        status: j['status'] as String,
        notes: j['notes'] as String?,
        customer: j['customer'] != null
            ? Customer.fromJson(j['customer'] as Map<String, dynamic>)
            : null,
      );

  @override
  List<Object?> get props => [id, status];
}

class VisitPhoto extends Equatable {
  const VisitPhoto({
    required this.id,
    required this.photoUrl,
    required this.photoType,
    required this.takenAt,
  });

  final int id;
  final String photoUrl;
  final String photoType;
  final String takenAt;

  factory VisitPhoto.fromJson(Map<String, dynamic> j) => VisitPhoto(
        id: j['id'] as int,
        photoUrl: j['photo_url'] as String,
        photoType: j['photo_type'] as String,
        takenAt: j['taken_at'] as String,
      );

  @override
  List<Object?> get props => [id];
}

class Visit extends Equatable {
  const Visit({
    required this.id,
    required this.jobId,
    required this.employeeId,
    required this.checkInIsMock,
    required this.durationMinutes,
    required this.photos,
    this.checkInTime,
    this.checkOutTime,
    this.checkInDistanceM,
    this.outcome,
    this.notes,
    this.signatureUrl,
    this.visitForm,
  });

  final int id;
  final int jobId;
  final int employeeId;
  final String? checkInTime;
  final String? checkOutTime;
  final int? checkInDistanceM;
  final bool checkInIsMock;
  final String? outcome;
  final String? notes;
  final String? signatureUrl;
  final int durationMinutes;
  final Map<String, dynamic>? visitForm;
  final List<VisitPhoto> photos;

  factory Visit.fromJson(Map<String, dynamic> j) => Visit(
        id: j['id'] as int,
        jobId: j['job_id'] as int,
        employeeId: j['employee_id'] as int,
        checkInTime: j['check_in_time'] as String?,
        checkOutTime: j['check_out_time'] as String?,
        checkInDistanceM: j['check_in_distance_m'] as int?,
        checkInIsMock: (j['check_in_is_mock'] as bool?) ?? false,
        outcome: j['outcome'] as String?,
        notes: j['notes'] as String?,
        signatureUrl: j['signature_url'] as String?,
        durationMinutes: (j['duration_minutes'] as int?) ?? 0,
        visitForm: (j['visit_form'] as Map?)?.cast<String, dynamic>(),
        photos: ((j['photos'] as List?) ?? const [])
            .map((e) => VisitPhoto.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  bool get isCheckedIn => checkInTime != null;
  bool get isClosed => checkOutTime != null;

  @override
  List<Object?> get props => [id, checkInTime, checkOutTime];
}

class LiveMapEntry extends Equatable {
  const LiveMapEntry({
    required this.employeeId,
    required this.employeeCode,
    required this.name,
    required this.lat,
    required this.lng,
    required this.timestamp,
    required this.currentStatus,
    this.batteryPct,
  });

  final int employeeId;
  final String employeeCode;
  final String name;
  final double lat;
  final double lng;
  final String timestamp;
  final String currentStatus;
  final int? batteryPct;

  factory LiveMapEntry.fromJson(Map<String, dynamic> j) => LiveMapEntry(
        employeeId: j['employee_id'] as int,
        employeeCode: j['employee_code'] as String,
        name: j['name'] as String,
        lat: (j['lat'] as num).toDouble(),
        lng: (j['lng'] as num).toDouble(),
        timestamp: j['timestamp'] as String,
        currentStatus: j['current_status'] as String,
        batteryPct: j['battery_pct'] as int?,
      );

  @override
  List<Object?> get props => [employeeId, timestamp];
}
