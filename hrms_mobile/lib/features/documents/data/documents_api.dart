import 'package:dio/dio.dart';

/// A letter HR issued to the employee (offer, appointment, confirmation …).
class EmployeeLetter {
  const EmployeeLetter({
    required this.id,
    required this.letterType,
    required this.title,
    required this.letterNumber,
    required this.issuedOn,
    required this.fileName,
    required this.mimeType,
  });

  final int id;
  final String letterType;
  final String title;
  final String? letterNumber;
  final String issuedOn;
  final String fileName;
  final String mimeType;

  factory EmployeeLetter.fromJson(Map<String, dynamic> j) => EmployeeLetter(
        id: j['id'] as int,
        letterType: j['letter_type'] as String? ?? 'other',
        title: j['title'] as String? ?? 'Letter',
        letterNumber: j['letter_number'] as String?,
        issuedOn: j['issued_on'] as String? ?? '',
        fileName: j['file_name'] as String? ?? 'letter.pdf',
        mimeType: j['mime_type'] as String? ?? 'application/pdf',
      );

  String get typeLabel => letterTypeLabels[letterType] ?? 'Letter';
}

const letterTypeLabels = {
  'offer': 'Offer letter',
  'appointment': 'Appointment letter',
  'confirmation': 'Confirmation letter',
  'increment': 'Increment letter',
  'promotion': 'Promotion letter',
  'experience': 'Experience letter',
  'relieving': 'Relieving letter',
  'termination': 'Termination letter',
  'warning': 'Warning letter',
  'other': 'Letter',
};

/// A company policy published to everyone.
class CompanyPolicy {
  const CompanyPolicy({
    required this.id,
    required this.title,
    required this.category,
    required this.description,
    required this.version,
    required this.effectiveDate,
    required this.fileName,
    required this.mimeType,
    required this.updatedAt,
  });

  final int id;
  final String title;
  final String category;
  final String? description;
  final String? version;
  final String? effectiveDate;
  final String fileName;
  final String mimeType;
  final String? updatedAt;

  factory CompanyPolicy.fromJson(Map<String, dynamic> j) => CompanyPolicy(
        id: j['id'] as int,
        title: j['title'] as String? ?? 'Policy',
        category: j['category'] as String? ?? 'other',
        description: j['description'] as String?,
        version: j['version'] as String?,
        effectiveDate: j['effective_date'] as String?,
        fileName: j['file_name'] as String? ?? 'policy.pdf',
        mimeType: j['mime_type'] as String? ?? 'application/pdf',
        updatedAt: j['updated_at'] as String?,
      );

  String get categoryLabel => policyCategoryLabels[category] ?? 'Other';
}

const policyCategoryLabels = {
  'hr': 'HR',
  'leave': 'Leave',
  'attendance': 'Attendance',
  'conduct': 'Code of conduct',
  'it': 'IT & security',
  'travel': 'Travel',
  'safety': 'Safety',
  'other': 'Other',
};

class DocumentsApi {
  DocumentsApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<EmployeeLetter>> myLetters() async {
    final res = await _dio.get<List<dynamic>>('$_v1/me/letters');
    return (res.data ?? const [])
        .map((e) => EmployeeLetter.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<CompanyPolicy>> policies() async {
    final res = await _dio.get<List<dynamic>>('$_v1/policies');
    return (res.data ?? const [])
        .map((e) => CompanyPolicy.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<int>> letterFile(int id) => _bytes('$_v1/issued-letters/$id/file');

  Future<List<int>> policyFile(int id) => _bytes('$_v1/policies/$id/file');

  Future<List<int>> _bytes(String path) async {
    final res = await _dio.get<List<int>>(
      path,
      options: Options(responseType: ResponseType.bytes),
    );
    final bytes = res.data ?? const <int>[];
    if (bytes.isEmpty) throw StateError('The file is empty');
    return bytes;
  }
}
