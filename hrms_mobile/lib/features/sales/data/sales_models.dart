import 'package:equatable/equatable.dart';

class Lead extends Equatable {
  const Lead({
    required this.id,
    required this.source,
    required this.stage,
    required this.expectedValue,
    required this.score,
    this.customerId,
    this.contactName,
    this.contactPhone,
    this.contactEmail,
    this.expectedCloseDate,
    this.assignedTo,
    this.nextAction,
    this.nextActionDate,
    this.notes,
    this.lostReason,
  });

  final int id;
  final int? customerId;
  final String? contactName;
  final String? contactPhone;
  final String? contactEmail;
  final String source;
  final String stage;
  final double expectedValue;
  final String? expectedCloseDate;
  final int? assignedTo;
  final int score;
  final String? nextAction;
  final String? nextActionDate;
  final String? notes;
  final String? lostReason;

  factory Lead.fromJson(Map<String, dynamic> j) => Lead(
        id: j['id'] as int,
        customerId: j['customer_id'] as int?,
        contactName: j['contact_name'] as String?,
        contactPhone: j['contact_phone'] as String?,
        contactEmail: j['contact_email'] as String?,
        source: j['source'] as String,
        stage: j['stage'] as String,
        expectedValue: double.tryParse(j['expected_value'].toString()) ?? 0,
        expectedCloseDate: j['expected_close_date'] as String?,
        assignedTo: j['assigned_to'] as int?,
        score: (j['score'] as int?) ?? 0,
        nextAction: j['next_action'] as String?,
        nextActionDate: j['next_action_date'] as String?,
        notes: j['notes'] as String?,
        lostReason: j['lost_reason'] as String?,
      );

  @override
  List<Object?> get props => [id, stage];
}

class PipelineColumn extends Equatable {
  const PipelineColumn({
    required this.stage,
    required this.leads,
    required this.totalValue,
    required this.count,
  });

  final String stage;
  final List<Lead> leads;
  final double totalValue;
  final int count;

  factory PipelineColumn.fromJson(Map<String, dynamic> j) => PipelineColumn(
        stage: j['stage'] as String,
        leads: ((j['leads'] as List?) ?? const [])
            .map((e) => Lead.fromJson(e as Map<String, dynamic>))
            .toList(),
        totalValue: double.tryParse(j['total_value'].toString()) ?? 0,
        count: (j['count'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [stage, count];
}

class Product extends Equatable {
  const Product({
    required this.id,
    required this.sku,
    required this.name,
    required this.unitPrice,
    required this.taxPct,
    this.description,
    this.category,
  });

  final int id;
  final String sku;
  final String name;
  final double unitPrice;
  final double taxPct;
  final String? description;
  final String? category;

  factory Product.fromJson(Map<String, dynamic> j) => Product(
        id: j['id'] as int,
        sku: j['sku'] as String,
        name: j['name'] as String,
        description: j['description'] as String?,
        category: j['category'] as String?,
        unitPrice: double.tryParse(j['unit_price'].toString()) ?? 0,
        taxPct: double.tryParse(j['tax_pct'].toString()) ?? 18,
      );

  @override
  List<Object?> get props => [id];
}

class SalesTarget extends Equatable {
  const SalesTarget({
    required this.id,
    required this.employeeId,
    required this.periodType,
    required this.periodStart,
    required this.periodEnd,
    required this.targetAmount,
    required this.achievedAmount,
    required this.commissionPct,
  });

  final int id;
  final int employeeId;
  final String periodType;
  final String periodStart;
  final String periodEnd;
  final double targetAmount;
  final double achievedAmount;
  final double commissionPct;

  factory SalesTarget.fromJson(Map<String, dynamic> j) => SalesTarget(
        id: j['id'] as int,
        employeeId: j['employee_id'] as int,
        periodType: j['period_type'] as String,
        periodStart: j['period_start'] as String,
        periodEnd: j['period_end'] as String,
        targetAmount: double.tryParse(j['target_amount'].toString()) ?? 0,
        achievedAmount: double.tryParse(j['achieved_amount'].toString()) ?? 0,
        commissionPct: double.tryParse(j['commission_pct'].toString()) ?? 0,
      );

  @override
  List<Object?> get props => [id, achievedAmount];
}

class TargetSummary extends Equatable {
  const TargetSummary({
    required this.target,
    required this.achievementPct,
    required this.commissionAmount,
  });

  final SalesTarget target;
  final double achievementPct;
  final double commissionAmount;

  factory TargetSummary.fromJson(Map<String, dynamic> j) => TargetSummary(
        target: SalesTarget.fromJson(j['target'] as Map<String, dynamic>),
        achievementPct:
            double.tryParse(j['achievement_pct'].toString()) ?? 0,
        commissionAmount:
            double.tryParse(j['commission_amount'].toString()) ?? 0,
      );

  @override
  List<Object?> get props => [target, achievementPct];
}

class Quote extends Equatable {
  const Quote({
    required this.id,
    required this.quoteNumber,
    required this.subtotal,
    required this.discountAmount,
    required this.taxAmount,
    required this.totalAmount,
    required this.status,
    this.notes,
  });

  final int id;
  final String quoteNumber;
  final double subtotal;
  final double discountAmount;
  final double taxAmount;
  final double totalAmount;
  final String status;
  final String? notes;

  factory Quote.fromJson(Map<String, dynamic> j) => Quote(
        id: j['id'] as int,
        quoteNumber: j['quote_number'] as String,
        subtotal: double.tryParse(j['subtotal'].toString()) ?? 0,
        discountAmount: double.tryParse(j['discount_amount'].toString()) ?? 0,
        taxAmount: double.tryParse(j['tax_amount'].toString()) ?? 0,
        totalAmount: double.tryParse(j['total_amount'].toString()) ?? 0,
        status: j['status'] as String,
        notes: j['notes'] as String?,
      );

  @override
  List<Object?> get props => [id, status];
}
