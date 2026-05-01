import 'package:equatable/equatable.dart';

class ApprovalItem extends Equatable {
  const ApprovalItem({
    required this.id,
    required this.requestType,
    required this.requestId,
    required this.title,
    this.summary,
    required this.status,
    required this.requestData,
    required this.initiatedAt,
  });

  final int id;
  final String requestType;
  final int requestId;
  final String title;
  final String? summary;
  final String status;
  final Map<String, dynamic> requestData;
  final String initiatedAt;

  factory ApprovalItem.fromJson(Map<String, dynamic> json) => ApprovalItem(
        id: json['id'] as int,
        requestType: json['request_type'] as String,
        requestId: json['request_id'] as int,
        title: (json['title'] as String?) ?? '',
        summary: json['summary'] as String?,
        status: json['status'] as String,
        requestData:
            (json['request_data'] as Map?)?.cast<String, dynamic>() ??
                <String, dynamic>{},
        initiatedAt: json['initiated_at'] as String,
      );

  @override
  List<Object?> get props => [id, status];
}

class ApprovalCount extends Equatable {
  const ApprovalCount({required this.requestType, required this.count});
  final String requestType;
  final int count;

  factory ApprovalCount.fromJson(Map<String, dynamic> json) => ApprovalCount(
        requestType: json['request_type'] as String,
        count: json['count'] as int,
      );

  @override
  List<Object?> get props => [requestType, count];
}

const Map<String, String> approvalTypeLabel = {
  'leave_request': 'Leave',
  'attendance_regularization': 'Regularization',
  'intern_expense': 'Intern expense',
};
