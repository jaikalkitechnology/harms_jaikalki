import 'package:equatable/equatable.dart';

class ComplaintListItem extends Equatable {
  const ComplaintListItem({
    required this.id,
    required this.ticketNumber,
    required this.complaintType,
    required this.privacyLevel,
    required this.severity,
    required this.status,
    required this.subject,
    required this.submittedAt,
    this.deadlineAt,
    required this.isAnonymous,
  });

  final int id;
  final String ticketNumber;
  final String complaintType;
  final String privacyLevel;
  final String severity;
  final String status;
  final String subject;
  final String submittedAt;
  final String? deadlineAt;
  final bool isAnonymous;

  factory ComplaintListItem.fromJson(Map<String, dynamic> json) =>
      ComplaintListItem(
        id: json['id'] as int,
        ticketNumber: json['ticket_number'] as String,
        complaintType: json['complaint_type'] as String,
        privacyLevel: json['privacy_level'] as String,
        severity: json['severity'] as String,
        status: json['status'] as String,
        subject: json['subject'] as String,
        submittedAt: json['submitted_at'] as String,
        deadlineAt: json['deadline_at'] as String?,
        isAnonymous: (json['is_anonymous'] as bool?) ?? false,
      );

  @override
  List<Object?> get props => [id];
}

class Resources {
  const Resources({
    required this.helplines,
    required this.policies,
    required this.externalResources,
  });

  final List<HelplineEntry> helplines;
  final List<PolicyEntry> policies;
  final List<ExternalResource> externalResources;

  factory Resources.fromJson(Map<String, dynamic> json) => Resources(
        helplines: ((json['helplines'] as List?) ?? const [])
            .map((e) => HelplineEntry.fromJson(e as Map<String, dynamic>))
            .toList(),
        policies: ((json['policies'] as List?) ?? const [])
            .map((e) => PolicyEntry.fromJson(e as Map<String, dynamic>))
            .toList(),
        externalResources: ((json['external_resources'] as List?) ?? const [])
            .map((e) => ExternalResource.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class HelplineEntry {
  const HelplineEntry({required this.name, required this.number});
  final String name;
  final String number;
  factory HelplineEntry.fromJson(Map<String, dynamic> json) => HelplineEntry(
        name: json['name'] as String,
        number: json['number'] as String,
      );
}

class PolicyEntry {
  const PolicyEntry({required this.title, required this.summary});
  final String title;
  final String summary;
  factory PolicyEntry.fromJson(Map<String, dynamic> json) => PolicyEntry(
        title: json['title'] as String,
        summary: json['summary'] as String,
      );
}

class ExternalResource {
  const ExternalResource({required this.name, required this.url});
  final String name;
  final String url;
  factory ExternalResource.fromJson(Map<String, dynamic> json) =>
      ExternalResource(
        name: json['name'] as String,
        url: json['url'] as String,
      );
}
