import 'package:equatable/equatable.dart';

class DwpField extends Equatable {
  const DwpField({
    required this.id,
    required this.key,
    required this.label,
    this.helpText,
    required this.fieldType,
    required this.isRequired,
    this.options,
    required this.displayOrder,
  });

  final int id;
  final String key;
  final String label;
  final String? helpText;
  final String fieldType;
  final bool isRequired;
  final List<dynamic>? options;
  final int displayOrder;

  factory DwpField.fromJson(Map<String, dynamic> json) => DwpField(
        id: json['id'] as int,
        key: json['key'] as String,
        label: json['label'] as String,
        helpText: json['help_text'] as String?,
        fieldType: json['field_type'] as String,
        isRequired: (json['is_required'] as bool?) ?? false,
        options: (json['options'] as List?)?.toList(),
        displayOrder: (json['display_order'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [id, key];
}

class DwpTemplate extends Equatable {
  const DwpTemplate({
    required this.id,
    required this.code,
    required this.name,
    this.description,
    required this.type,
    required this.fields,
  });

  final int id;
  final String code;
  final String name;
  final String? description;
  final String type;
  final List<DwpField> fields;

  factory DwpTemplate.fromJson(Map<String, dynamic> json) => DwpTemplate(
        id: json['id'] as int,
        code: json['code'] as String,
        name: json['name'] as String,
        description: json['description'] as String?,
        type: json['type'] as String,
        fields: ((json['fields'] as List?) ?? const [])
            .map((e) => DwpField.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [id];
}

class DwpTemplateWithPrefill extends Equatable {
  const DwpTemplateWithPrefill({
    required this.template,
    required this.prefill,
    this.linkedMorningId,
    required this.streakDays,
  });

  final DwpTemplate template;
  final Map<String, dynamic> prefill;
  final int? linkedMorningId;
  final int streakDays;

  factory DwpTemplateWithPrefill.fromJson(Map<String, dynamic> json) =>
      DwpTemplateWithPrefill(
        template: DwpTemplate.fromJson(json['template'] as Map<String, dynamic>),
        prefill: (json['prefill'] as Map?)?.cast<String, dynamic>() ??
            <String, dynamic>{},
        linkedMorningId: json['linked_morning_id'] as int?,
        streakDays: (json['streak_days'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [template, streakDays];
}

class DwpSubmissionField extends Equatable {
  const DwpSubmissionField({
    required this.fieldKey,
    this.value,
    this.fileUrl,
  });

  final String fieldKey;
  final String? value;
  final String? fileUrl;

  factory DwpSubmissionField.fromJson(Map<String, dynamic> json) =>
      DwpSubmissionField(
        fieldKey: json['field_key'] as String,
        value: json['value'] as String?,
        fileUrl: json['file_url'] as String?,
      );

  @override
  List<Object?> get props => [fieldKey, value, fileUrl];
}

class DwpSubmission extends Equatable {
  const DwpSubmission({
    required this.id,
    required this.type,
    required this.date,
    required this.submittedAt,
    required this.fields,
    this.totalHours,
    this.moodRating,
  });

  final int id;
  final String type;
  final String date;
  final String submittedAt;
  final List<DwpSubmissionField> fields;
  final num? totalHours;
  final int? moodRating;

  factory DwpSubmission.fromJson(Map<String, dynamic> json) => DwpSubmission(
        id: json['id'] as int,
        type: json['type'] as String,
        date: json['date'] as String,
        submittedAt: json['submitted_at'] as String,
        totalHours: num.tryParse('${json['total_hours']}'),
        moodRating: json['mood_rating'] as int?,
        fields: ((json['fields'] as List?) ?? const [])
            .map((e) => DwpSubmissionField.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [id];
}
