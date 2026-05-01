import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/verification_api.dart';
import '../data/verification_models.dart';

class VerificationFormPage extends StatefulWidget {
  const VerificationFormPage({super.key, required this.verificationId});
  final int verificationId;

  @override
  State<VerificationFormPage> createState() => _VerificationFormPageState();
}

class _VerificationFormPageState extends State<VerificationFormPage> {
  late Future<({VerificationJob job, VerificationTemplate template})> _future;
  final Map<String, dynamic> _values = {};
  final List<String> _photos = [];
  String _result = 'positive';
  String _remarks = '';
  String? _signatureUrl;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({VerificationJob job, VerificationTemplate template})> _load() async {
    final api = sl<VerificationApi>();
    final queue = await api.myQueue();
    final job = queue.firstWhere(
      (j) => j.id == widget.verificationId,
      orElse: () => throw StateError('Job not found'),
    );
    final template = await api.getTemplate(job.templateId);
    return (job: job, template: template);
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

  Future<void> _start(VerificationJob job) async {
    setState(() => _busy = true);
    try {
      await sl<VerificationApi>().startJob(job.id);
      _toast('Started');
      setState(() => _future = _load());
    } catch (_) {
      _toast('Could not start', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _addPhoto(String key) async {
    // In production: image_picker → upload → real URL.
    final url =
        'https://example.com/$key-${DateTime.now().millisecondsSinceEpoch}.jpg';
    setState(() => _photos.add(url));
    _toast('Photo added');
  }

  Future<void> _captureSignature() async {
    setState(() => _signatureUrl =
        'https://example.com/sig-${DateTime.now().millisecondsSinceEpoch}.png');
    _toast('Signature captured');
  }

  Future<void> _submit(VerificationJob job, VerificationTemplate template) async {
    setState(() => _busy = true);
    try {
      final pos = await _getPosition();
      await sl<VerificationApi>().submit(
        id: job.id,
        formData: _values,
        result: _result,
        photos: _photos.isEmpty ? null : _photos,
        signatureUrl: _signatureUrl,
        lat: pos?.latitude,
        lng: pos?.longitude,
        remarks: _remarks.isEmpty ? null : _remarks,
      );
      _toast('Submitted for audit');
      if (mounted) Navigator.of(context).pop(true);
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Submit failed')
          : 'Submit failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _buildField(TemplateField f) {
    final label = '${f.label}${f.required ? ' *' : ''}';
    switch (f.fieldType) {
      case 'dropdown':
        return DropdownButtonFormField<String>(
          decoration: InputDecoration(labelText: label),
          value: _values[f.key] as String?,
          items: (f.options ?? const [])
              .map((o) => DropdownMenuItem(value: o, child: Text(o)))
              .toList(),
          onChanged: (v) => setState(() => _values[f.key] = v),
        );
      case 'checkbox':
        return CheckboxListTile(
          contentPadding: EdgeInsets.zero,
          title: Text(label),
          value: (_values[f.key] as bool?) ?? false,
          onChanged: (v) => setState(() => _values[f.key] = v ?? false),
        );
      case 'number':
        return TextFormField(
          decoration: InputDecoration(labelText: label),
          keyboardType: TextInputType.number,
          onChanged: (v) =>
              _values[f.key] = int.tryParse(v) ?? double.tryParse(v) ?? v,
        );
      case 'date':
        return TextFormField(
          decoration: InputDecoration(
            labelText: label,
            hintText: 'YYYY-MM-DD',
          ),
          onChanged: (v) => _values[f.key] = v,
        );
      case 'textarea':
        return TextFormField(
          decoration: InputDecoration(labelText: label),
          maxLines: 3,
          onChanged: (v) => _values[f.key] = v,
        );
      default:
        return TextFormField(
          decoration: InputDecoration(labelText: label),
          onChanged: (v) => _values[f.key] = v,
        );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Verification')),
      body: FutureBuilder<({VerificationJob job, VerificationTemplate template})>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final job = snap.data!.job;
          final template = snap.data!.template;
          final canEdit =
              job.status == 'in_progress' || job.status == 'pending';

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
                          Text(job.subjectName,
                              style: theme.textTheme.titleLarge),
                          const SizedBox(height: 4),
                          Text(
                            '${job.ticketNumber} · ${template.name}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: AppColors.brandBrownLight,
                            ),
                          ),
                          if (job.address != null) ...[
                            const SizedBox(height: 8),
                            Text(job.address!,
                                style: theme.textTheme.bodyMedium),
                          ],
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  if (job.status == 'pending') ...[
                    SizedBox(
                      height: 56,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.play_arrow),
                        label: const Text('Start verification'),
                        onPressed: _busy ? null : () => _start(job),
                      ),
                    ),
                  ] else if (canEdit) ...[
                    Text('★ FINDINGS',
                        style: theme.textTheme.labelSmall?.copyWith(
                          color: AppColors.brandGoldDark,
                        )),
                    const SizedBox(height: 8),
                    ...template.fields.map((f) => Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _buildField(f),
                        )),
                    if (template.photoRequirements != null) ...[
                      const SizedBox(height: 8),
                      Text(
                          '★ PHOTOS (${_photos.length}/${template.photoRequirements!.length})',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.brandGoldDark,
                          )),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        children: template.photoRequirements!
                            .map((p) => OutlinedButton.icon(
                                  icon: const Icon(Icons.camera_alt, size: 16),
                                  label: Text(
                                      '${p.label}${p.required ? '*' : ''}'),
                                  onPressed:
                                      _busy ? null : () => _addPhoto(p.key),
                                ))
                            .toList(),
                      ),
                    ],
                    if (template.signatureRequired) ...[
                      const SizedBox(height: 16),
                      OutlinedButton.icon(
                        icon: Icon(
                          _signatureUrl != null
                              ? Icons.check_circle
                              : Icons.draw_outlined,
                          color: _signatureUrl != null
                              ? AppColors.success
                              : null,
                        ),
                        label: Text(_signatureUrl != null
                            ? 'Signature captured'
                            : 'Capture signature *'),
                        onPressed: _busy ? null : _captureSignature,
                      ),
                    ],
                    const SizedBox(height: 16),
                    DropdownButtonFormField<String>(
                      decoration: const InputDecoration(labelText: 'Result *'),
                      value: _result,
                      items: const [
                        DropdownMenuItem(value: 'positive', child: Text('Positive')),
                        DropdownMenuItem(value: 'negative', child: Text('Negative')),
                        DropdownMenuItem(
                            value: 'unable_to_verify',
                            child: Text('Unable to verify')),
                        DropdownMenuItem(value: 'partial', child: Text('Partial')),
                      ],
                      onChanged: (v) => setState(() => _result = v ?? 'positive'),
                    ),
                    const SizedBox(height: 8),
                    TextField(
                      decoration: const InputDecoration(labelText: 'Remarks'),
                      maxLines: 3,
                      onChanged: (v) => _remarks = v,
                    ),
                    const SizedBox(height: 16),
                    SizedBox(
                      height: 56,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.send),
                        label: const Text('Submit for audit'),
                        onPressed:
                            _busy ? null : () => _submit(job, template),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: AppColors.success,
                        ),
                      ),
                    ),
                  ] else ...[
                    Card(
                      color: AppColors.brandBrown50,
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Text(
                          'This verification is in "${job.status}" state and cannot be edited from the field app.',
                          style: theme.textTheme.bodyMedium,
                        ),
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
