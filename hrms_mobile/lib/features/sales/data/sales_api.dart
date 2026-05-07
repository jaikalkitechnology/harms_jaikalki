import 'package:dio/dio.dart';

import 'sales_models.dart';

class SalesApi {
  SalesApi(this._dio);
  final Dio _dio;

  static const _v1 = '/api/v1';

  Future<List<Lead>> myLeads({String? stage}) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/sales/leads',
      queryParameters: {
        'mine': true,
        if (stage != null) 'stage': stage,
      },
    );
    return (res.data ?? const [])
        .map((e) => Lead.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Lead> createLead(Map<String, dynamic> payload) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/sales/leads',
      data: payload,
    );
    return Lead.fromJson(res.data!);
  }

  Future<Lead> updateStage(int leadId, String stage,
      {String? lostReason}) async {
    final res = await _dio.patch<Map<String, dynamic>>(
      '$_v1/sales/leads/$leadId/stage',
      data: {
        'stage': stage,
        if (lostReason != null) 'lost_reason': lostReason,
      },
    );
    return Lead.fromJson(res.data!);
  }

  Future<List<LeadActivity>> leadActivities(int leadId) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/sales/leads/$leadId/activities',
    );
    return (res.data ?? const [])
        .map((e) => LeadActivity.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<LeadActivity> addLeadComment(int leadId, String body) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/sales/leads/$leadId/comments',
      data: {'body': body},
    );
    return LeadActivity.fromJson(res.data!);
  }

  Future<List<PipelineColumn>> myPipeline() async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/sales/pipeline',
      queryParameters: {'mine': true},
    );
    return (res.data ?? const [])
        .map((e) => PipelineColumn.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Product>> products() async {
    final res = await _dio.get<List<dynamic>>('$_v1/sales/products');
    return (res.data ?? const [])
        .map((e) => Product.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<Quote> createQuote({
    required int customerId,
    required List<Map<String, dynamic>> lineItems,
    double discountPct = 0,
    String? notes,
    int? leadId,
  }) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/sales/quotes',
      data: {
        'customer_id': customerId,
        'line_items': lineItems,
        'discount_pct': discountPct,
        if (notes != null) 'notes': notes,
        if (leadId != null) 'lead_id': leadId,
      },
    );
    return Quote.fromJson(res.data!);
  }

  Future<TargetSummary?> myTarget() async {
    final res = await _dio.get<dynamic>('$_v1/sales/targets/me');
    if (res.data == null) return null;
    return TargetSummary.fromJson(res.data as Map<String, dynamic>);
  }

  Future<SalesTarget> refreshTarget(int targetId) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/sales/targets/$targetId/recompute',
    );
    return SalesTarget.fromJson(res.data!);
  }

  Future<void> logPromotion({
    required String eventName,
    required String activityDate,
    String? location,
    int bannersPlaced = 0,
    int brochuresDistributed = 0,
    int demosGiven = 0,
    int leadsCollected = 0,
    String? notes,
  }) async {
    await _dio.post(
      '$_v1/sales/promotions',
      data: {
        'event_name': eventName,
        'activity_date': activityDate,
        if (location != null) 'location': location,
        'banners_placed': bannersPlaced,
        'brochures_distributed': brochuresDistributed,
        'demos_given': demosGiven,
        'leads_collected': leadsCollected,
        if (notes != null) 'notes': notes,
      },
    );
  }
}
