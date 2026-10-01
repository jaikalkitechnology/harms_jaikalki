import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/field_api.dart';
import '../data/field_models.dart';

class FieldVisitPage extends StatefulWidget {
  const FieldVisitPage({super.key, required this.jobId});
  final int jobId;

  @override
  State<FieldVisitPage> createState() => _FieldVisitPageState();
}

class _FieldVisitPageState extends State<FieldVisitPage> {
  late Future<FieldJob> _jobFuture;
  Visit? _visit;
  bool _busy = false;

  final _formKey = GlobalKey<FormState>();
  final _competitorCtrl = TextEditingController();
  final _stockCtrl = TextEditingController();
  final _outcomeCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _jobFuture = _loadJob();
  }

  Future<FieldJob> _loadJob() async {
    final jobs = await sl<FieldApi>().myJobs();
    return jobs.firstWhere(
      (j) => j.id == widget.jobId,
      orElse: () => throw StateError('Job not found'),
    );
  }

  @override
  void dispose() {
    _competitorCtrl.dispose();
    _stockCtrl.dispose();
    _outcomeCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }

  Future<Position?> _getPosition() async {
    final perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      final req = await Geolocator.requestPermission();
      if (req == LocationPermission.denied ||
          req == LocationPermission.deniedForever) {
        return null;
      }
    }
    try {
      return await Geolocator.getCurrentPosition(
        desiredAccuracy: LocationAccuracy.high,
      );
    } catch (_) {
      return null;
    }
  }

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? AppColors.error : AppColors.success,
      ),
    );
  }

  Future<void> _checkIn(FieldJob job) async {
    setState(() => _busy = true);
    try {
      final pos = await _getPosition();
      if (pos == null) {
        _toast('Could not get GPS location', error: true);
        return;
      }
      final visit = await sl<FieldApi>().checkIn(
        jobId: job.id,
        lat: pos.latitude,
        lng: pos.longitude,
        // In a real device build, capture a selfie via image_picker and upload
        // first; here we send a placeholder URL.
        selfieUrl: 'https://example.com/selfie.jpg',
        isMock: pos.isMocked,
      );
      setState(() => _visit = visit);
      _toast('Checked in (${visit.checkInDistanceM ?? "?"} m from store)');
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Check-in failed')
          : 'Check-in failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _submitForm() async {
    if (_visit == null) return;
    if (!_formKey.currentState!.validate()) return;
    setState(() => _busy = true);
    try {
      final visit = await sl<FieldApi>().submitVisitForm(
        visitId: _visit!.id,
        visitForm: {
          'competitor_seen': _competitorCtrl.text.trim(),
          'stock_level': _stockCtrl.text.trim(),
        },
      );
      setState(() => _visit = visit);
      _toast('Visit form saved');
    } catch (_) {
      _toast('Could not save form', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _addPhoto(String type) async {
    if (_visit == null) return;
    setState(() => _busy = true);
    try {
      // In real builds: image_picker → upload → real URL.
      await sl<FieldApi>().addPhoto(
        visitId: _visit!.id,
        photoUrl: 'https://example.com/$type-${DateTime.now().millisecondsSinceEpoch}.jpg',
        photoType: type,
        watermarked: true,
      );
      final refreshed = await sl<FieldApi>().getVisit(_visit!.id);
      setState(() => _visit = refreshed);
      _toast('Photo added ($type)');
    } catch (_) {
      _toast('Could not add photo', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _checkOut() async {
    if (_visit == null) return;
    setState(() => _busy = true);
    try {
      final pos = await _getPosition();
      final visit = await sl<FieldApi>().checkOut(
        visitId: _visit!.id,
        lat: pos?.latitude,
        lng: pos?.longitude,
        outcome: _outcomeCtrl.text.trim().isEmpty
            ? null
            : _outcomeCtrl.text.trim(),
        notes: _notesCtrl.text.trim().isEmpty ? null : _notesCtrl.text.trim(),
        signatureUrl: 'https://example.com/sig.png',
      );
      setState(() => _visit = visit);
      _toast('Visit completed (${visit.durationMinutes} min)');
      if (mounted) Navigator.of(context).pop(true);
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Check-out failed')
          : 'Check-out failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Field Visit')),
      body: FutureBuilder<FieldJob>(
        future: _jobFuture,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final job = snap.data!;
          final cust = job.customer;
          final visit = _visit;

          return Stack(
            children: [
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(cust?.name ?? 'Customer',
                              style: theme.textTheme.titleLarge),
                          const SizedBox(height: 6),
                          Text(
                            '${job.jobType.replaceAll('_', ' ')} · ${job.priority}',
                            style: theme.textTheme.bodyMedium?.copyWith(
                              color: AppColors.textMuted,
                            ),
                          ),
                          if (cust?.address != null) ...[
                            const SizedBox(height: 8),
                            Text(cust!.address!,
                                style: theme.textTheme.bodySmall),
                          ],
                          if (visit != null && visit.checkInDistanceM != null) ...[
                            const SizedBox(height: 10),
                            Row(
                              children: [
                                Icon(Icons.gps_fixed,
                                    size: 16,
                                    color: AppColors.brandGoldDark),
                                const SizedBox(width: 4),
                                Text(
                                  'Checked in ${visit.checkInDistanceM} m from store',
                                  style: theme.textTheme.bodySmall,
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (visit == null) ...[
                    SizedBox(
                      height: 56,
                      child: ElevatedButton.icon(
                        onPressed: _busy ? null : () => _checkIn(job),
                        icon: const Icon(Icons.login),
                        label: const Text('Check in & start visit'),
                      ),
                    ),
                  ] else ...[
                    Text('★ VISIT FORM',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: AppColors.brandGoldDark,
                        )),
                    const SizedBox(height: 8),
                    Form(
                      key: _formKey,
                      child: Column(
                        children: [
                          TextFormField(
                            controller: _competitorCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Competitor seen',
                            ),
                          ),
                          const SizedBox(height: 8),
                          TextFormField(
                            controller: _stockCtrl,
                            decoration: const InputDecoration(
                              labelText: 'Stock level',
                            ),
                          ),
                          const SizedBox(height: 8),
                          OutlinedButton.icon(
                            onPressed: _busy ? null : _submitForm,
                            icon: const Icon(Icons.save),
                            label: const Text('Save form'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text('★ PHOTOS (${visit.photos.length})',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: AppColors.brandGoldDark,
                        )),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      children: [
                        OutlinedButton.icon(
                          onPressed: _busy ? null : () => _addPhoto('storefront'),
                          icon: const Icon(Icons.storefront),
                          label: const Text('Storefront'),
                        ),
                        OutlinedButton.icon(
                          onPressed: _busy ? null : () => _addPhoto('shelf'),
                          icon: const Icon(Icons.view_quilt),
                          label: const Text('Shelf'),
                        ),
                        OutlinedButton.icon(
                          onPressed: _busy ? null : () => _addPhoto('product'),
                          icon: const Icon(Icons.inventory_2),
                          label: const Text('Product'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: _outcomeCtrl,
                      decoration: const InputDecoration(
                        labelText: 'Outcome (e.g. order_placed)',
                      ),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      controller: _notesCtrl,
                      maxLines: 3,
                      decoration: const InputDecoration(
                        labelText: 'Notes',
                      ),
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      height: 56,
                      child: ElevatedButton.icon(
                        onPressed: _busy ? null : _checkOut,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.success,
                        ),
                        icon: const Icon(Icons.logout),
                        label: const Text('End visit'),
                      ),
                    ),
                  ],
                  const SizedBox(height: 32),
                ],
              ),
              if (_busy)
                const Positioned.fill(
                  child: ColoredBox(
                    color: Colors.black26,
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
