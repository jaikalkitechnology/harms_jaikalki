import 'package:equatable/equatable.dart';

class Asset extends Equatable {
  const Asset({
    required this.id,
    required this.assetTag,
    required this.name,
    required this.category,
    required this.condition,
    required this.status,
    this.brand,
    this.model,
    this.specs = const {},
    this.parentAssetId,
    this.isUsable = true,
    this.serialNumber,
    this.warrantyUntil,
    this.assignedTo,
    this.assignedAt,
  });

  final int id;
  final String assetTag;
  final String name;
  final String category;
  final String? brand;
  final String? model;

  /// Configuration, keyed by the category's spec fields (e.g. ram).
  final Map<String, String> specs;

  /// Set when this is an accessory of another asset (e.g. a charger).
  final int? parentAssetId;
  final bool isUsable;
  final String? serialNumber;
  final String? warrantyUntil;
  final String condition;
  final String status;
  final int? assignedTo;
  final String? assignedAt;

  String get makeModel =>
      [brand, model].where((s) => s != null && s.isNotEmpty).join(' ');

  factory Asset.fromJson(Map<String, dynamic> j) => Asset(
        id: j['id'] as int,
        assetTag: j['asset_tag'] as String,
        name: j['name'] as String,
        category: j['category'] as String,
        brand: j['brand'] as String?,
        model: j['model'] as String?,
        specs: ((j['specs'] as Map?) ?? const {})
            .map((k, v) => MapEntry(k.toString(), v.toString())),
        parentAssetId: j['parent_asset_id'] as int?,
        isUsable: (j['is_usable'] as bool?) ?? true,
        serialNumber: j['serial_number'] as String?,
        warrantyUntil: j['warranty_until'] as String?,
        condition: j['condition'] as String,
        status: j['status'] as String,
        assignedTo: j['assigned_to'] as int?,
        assignedAt: j['assigned_at'] as String?,
      );

  @override
  List<Object?> get props => [id, status, condition];
}

class AssetCategory extends Equatable {
  const AssetCategory({
    required this.code,
    required this.name,
    this.isAccessory = false,
    this.specFields = const [],
  });

  final String code;
  final String name;
  final bool isAccessory;

  /// (key, label) pairs, in display order.
  final List<(String, String)> specFields;

  factory AssetCategory.fromJson(Map<String, dynamic> j) => AssetCategory(
        code: j['code'] as String,
        name: j['name'] as String,
        isAccessory: (j['is_accessory'] as bool?) ?? false,
        specFields: ((j['spec_fields'] as List?) ?? const [])
            .map((f) => (
                  (f as Map)['key'].toString(),
                  f['label'].toString(),
                ))
            .toList(),
      );

  @override
  List<Object?> get props => [code];
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


class Visitor extends Equatable {
  const Visitor({
    required this.id,
    required this.fullName,
    required this.purpose,
    required this.hostEmployeeId,
    required this.expectedAt,
    required this.qrToken,
    required this.status,
    this.contactPhone,
    this.contactEmail,
    this.company,
    this.checkedInAt,
    this.checkedOutAt,
    this.badgeNumber,
  });

  final int id;
  final String fullName;
  final String? contactPhone;
  final String? contactEmail;
  final String? company;
  final String purpose;
  final int hostEmployeeId;
  final String expectedAt;
  final String qrToken;
  final String? checkedInAt;
  final String? checkedOutAt;
  final String? badgeNumber;
  final String status;

  factory Visitor.fromJson(Map<String, dynamic> j) => Visitor(
        id: j['id'] as int,
        fullName: j['full_name'] as String,
        contactPhone: j['contact_phone'] as String?,
        contactEmail: j['contact_email'] as String?,
        company: j['company'] as String?,
        purpose: j['purpose'] as String,
        hostEmployeeId: j['host_employee_id'] as int,
        expectedAt: j['expected_at'] as String,
        qrToken: j['qr_token'] as String,
        checkedInAt: j['checked_in_at'] as String?,
        checkedOutAt: j['checked_out_at'] as String?,
        badgeNumber: j['badge_number'] as String?,
        status: j['status'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}
