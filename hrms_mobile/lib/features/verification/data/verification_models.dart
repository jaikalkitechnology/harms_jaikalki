import 'package:equatable/equatable.dart';

class TemplateField extends Equatable {
  const TemplateField({
    required this.key,
    required this.label,
    required this.fieldType,
    required this.required,
    this.options,
    this.helpText,
  });

  final String key;
  final String label;
  final String fieldType;
  final bool required;
  final List<String>? options;
  final String? helpText;

  factory TemplateField.fromJson(Map<String, dynamic> j) => TemplateField(
        key: j['key'] as String,
        label: j['label'] as String,
        fieldType: j['field_type'] as String,
        required: (j['required'] as bool?) ?? false,
        options: (j['options'] as List?)?.map((e) => e.toString()).toList(),
        helpText: j['help_text'] as String?,
      );

  @override
  List<Object?> get props => [key];
}

class PhotoRequirement extends Equatable {
  const PhotoRequirement({
    required this.key,
    required this.label,
    required this.required,
  });

  final String key;
  final String label;
  final bool required;

  factory PhotoRequirement.fromJson(Map<String, dynamic> j) =>
      PhotoRequirement(
        key: j['key'] as String,
        label: j['label'] as String,
        required: (j['required'] as bool?) ?? true,
      );

  @override
  List<Object?> get props => [key];
}

class VerificationTemplate extends Equatable {
  const VerificationTemplate({
    required this.id,
    required this.code,
    required this.name,
    required this.type,
    required this.fields,
    required this.signatureRequired,
    required this.slaHours,
    this.description,
    this.photoRequirements,
  });

  final int id;
  final String code;
  final String name;
  final String type;
  final String? description;
  final List<TemplateField> fields;
  final List<PhotoRequirement>? photoRequirements;
  final bool signatureRequired;
  final int slaHours;

  factory VerificationTemplate.fromJson(Map<String, dynamic> j) =>
      VerificationTemplate(
        id: j['id'] as int,
        code: j['code'] as String,
        name: j['name'] as String,
        type: j['type'] as String,
        description: j['description'] as String?,
        fields: ((j['fields'] as List?) ?? const [])
            .map((e) => TemplateField.fromJson(e as Map<String, dynamic>))
            .toList(),
        photoRequirements: (j['photo_requirements'] as List?)
            ?.map((e) => PhotoRequirement.fromJson(e as Map<String, dynamic>))
            .toList(),
        signatureRequired: (j['signature_required'] as bool?) ?? false,
        slaHours: (j['sla_hours'] as int?) ?? 48,
      );

  @override
  List<Object?> get props => [id];
}

class VerificationJob extends Equatable {
  const VerificationJob({
    required this.id,
    required this.ticketNumber,
    required this.templateId,
    required this.type,
    required this.subjectName,
    required this.subjectData,
    required this.assignedAt,
    required this.status,
    required this.fraudFlagsCount,
    this.address,
    this.contactPhone,
    this.requestedByOrg,
    this.deadlineAt,
    this.formData,
    this.photos,
    this.signatureUrl,
    this.result,
    this.remarks,
  });

  final int id;
  final String ticketNumber;
  final int templateId;
  final String type;
  final String subjectName;
  final Map<String, dynamic> subjectData;
  final String? address;
  final String? contactPhone;
  final String? requestedByOrg;
  final String assignedAt;
  final String? deadlineAt;
  final String status;
  final Map<String, dynamic>? formData;
  final List<dynamic>? photos;
  final String? signatureUrl;
  final String? result;
  final String? remarks;
  final int fraudFlagsCount;

  factory VerificationJob.fromJson(Map<String, dynamic> j) => VerificationJob(
        id: j['id'] as int,
        ticketNumber: j['ticket_number'] as String,
        templateId: j['template_id'] as int,
        type: j['type'] as String,
        subjectName: j['subject_name'] as String,
        subjectData:
            (j['subject_data'] as Map?)?.cast<String, dynamic>() ?? const {},
        address: j['address'] as String?,
        contactPhone: j['contact_phone'] as String?,
        requestedByOrg: j['requested_by_org'] as String?,
        assignedAt: j['assigned_at'] as String,
        deadlineAt: j['deadline_at'] as String?,
        status: j['status'] as String,
        formData: (j['form_data'] as Map?)?.cast<String, dynamic>(),
        photos: j['photos'] as List?,
        signatureUrl: j['signature_url'] as String?,
        result: j['result'] as String?,
        remarks: j['remarks'] as String?,
        fraudFlagsCount: ((j['fraud_flags'] as List?) ?? const []).length,
      );

  @override
  List<Object?> get props => [id, status];
}
