import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

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
  // Required photos collected per template.photo_requirements (key -> url)
  final Map<String, String> _photoSlots = {};
  // Photos for in-form `photo` field type (key -> url)
  final Map<String, String> _fieldPhotos = {};
  String _result = 'positive';
  String _remarks = '';
  String? _signatureUrl;
  bool _busy = false;
  // Per-key uploading flags so individual buttons can show their own spinner.
  final Set<String> _uploading = {};

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

  /// Ask the user whether to grab the photo from the camera or gallery,
  /// then capture and upload it. Returns the uploaded URL on success.
  Future<String?> _pickAndUpload({
    required String kind,
    required String fieldKey,
  }) async {
    final picker = ImagePicker();

    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Take a photo'),
              onTap: () => Navigator.pop(ctx, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Pick from gallery'),
              onTap: () => Navigator.pop(ctx, ImageSource.gallery),
            ),
            ListTile(
              leading: const Icon(Icons.close),
              title: const Text('Cancel'),
              onTap: () => Navigator.pop(ctx),
            ),
          ],
        ),
      ),
    );
    if (source == null) return null;

    XFile? picked;
    try {
      picked = await picker.pickImage(
        source: source,
        imageQuality: 75,
        maxWidth: 2000,
      );
    } on Exception catch (e) {
      _toast('Camera/gallery error: $e', error: true);
      return null;
    }
    if (picked == null) {
      // User cancelled inside picker.
      return null;
    }

    setState(() => _uploading.add(fieldKey));
    try {
      final url = await sl<VerificationApi>().uploadFile(
        file: picked,
        kind: kind,
        fieldKey: fieldKey,
      );
      _toast('Uploaded');
      return url;
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Upload failed')
          : 'Upload failed (${e.message ?? "network"})';
      _toast(msg, error: true);
      return null;
    } catch (e) {
      _toast('Upload failed: $e', error: true);
      return null;
    } finally {
      if (mounted) setState(() => _uploading.remove(fieldKey));
    }
  }

  Future<void> _capturePhotoSlot(String key) async {
    final url = await _pickAndUpload(kind: 'photo', fieldKey: key);
    if (url != null && mounted) {
      setState(() => _photoSlots[key] = url);
    }
  }

  Future<void> _captureFieldPhoto(String key) async {
    final url = await _pickAndUpload(kind: 'photo', fieldKey: key);
    if (url != null && mounted) {
      setState(() {
        _fieldPhotos[key] = url;
        _values[key] = url;
      });
    }
  }

  Future<void> _captureSignature() async {
    final url = await _pickAndUpload(kind: 'signature', fieldKey: 'signature');
    if (url != null && mounted) {
      setState(() => _signatureUrl = url);
    }
  }

  Future<void> _submit(VerificationJob job, VerificationTemplate template) async {
    // Pre-flight required-photo check so the user gets a clear message
    // before the server bounces them.
    final missing = (template.photoRequirements ?? const [])
        .where((p) => p.required && !_photoSlots.containsKey(p.key))
        .map((p) => p.label)
        .toList();
    if (missing.isNotEmpty) {
      _toast('Missing photos: ${missing.join(", ")}', error: true);
      return;
    }
    if (template.signatureRequired && _signatureUrl == null) {
      _toast('Signature is required', error: true);
      return;
    }

    setState(() => _busy = true);
    try {
      final pos = await _getPosition();
      final photos = _photoSlots.values.toList();
      await sl<VerificationApi>().submit(
        id: job.id,
        formData: _values,
        result: _result,
        photos: photos.isEmpty ? null : photos,
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
      case 'photo':
        return _PhotoTile(
          label: label,
          url: _fieldPhotos[f.key],
          uploading: _uploading.contains(f.key),
          onCapture: () => _captureFieldPhoto(f.key),
        );
      case 'signature':
        return _PhotoTile(
          label: label,
          url: _values[f.key] as String?,
          uploading: _uploading.contains(f.key),
          icon: Icons.draw_outlined,
          onCapture: () async {
            final url = await _pickAndUpload(kind: 'signature', fieldKey: f.key);
            if (url != null && mounted) {
              setState(() => _values[f.key] = url);
            }
          },
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
                              color: AppColors.textMuted,
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
                    if (template.photoRequirements != null &&
                        template.photoRequirements!.isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Text(
                          '★ PHOTOS (${_photoSlots.length}/${template.photoRequirements!.length})',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.brandGoldDark,
                          )),
                      const SizedBox(height: 8),
                      Column(
                        children: template.photoRequirements!.map((p) {
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 8),
                            child: _PhotoTile(
                              label: '${p.label}${p.required ? '*' : ''}',
                              url: _photoSlots[p.key],
                              uploading: _uploading.contains(p.key),
                              onCapture:
                                  _busy ? null : () => _capturePhotoSlot(p.key),
                            ),
                          );
                        }).toList(),
                      ),
                    ],
                    if (template.signatureRequired) ...[
                      const SizedBox(height: 16),
                      _PhotoTile(
                        label: _signatureUrl != null
                            ? 'Signature captured'
                            : 'Capture signature *',
                        url: _signatureUrl,
                        uploading: _uploading.contains('signature'),
                        icon: Icons.draw_outlined,
                        onCapture: _busy ? null : _captureSignature,
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

class _PhotoTile extends StatelessWidget {
  const _PhotoTile({
    required this.label,
    required this.url,
    required this.uploading,
    required this.onCapture,
    this.icon = Icons.camera_alt,
  });

  final String label;
  final String? url;
  final bool uploading;
  final VoidCallback? onCapture;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    final hasPhoto = url != null && url!.isNotEmpty;
    return InkWell(
      borderRadius: BorderRadius.circular(8),
      onTap: uploading ? null : onCapture,
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          border: Border.all(
            color: hasPhoto
                ? AppColors.success
                : Colors.black.withOpacity(0.15),
          ),
          borderRadius: BorderRadius.circular(8),
          color: hasPhoto ? AppColors.success.withOpacity(0.05) : null,
        ),
        child: Row(
          children: [
            if (hasPhoto)
              ClipRRect(
                borderRadius: BorderRadius.circular(6),
                child: Image.network(
                  url!,
                  width: 56,
                  height: 56,
                  fit: BoxFit.cover,
                  errorBuilder: (_, __, ___) => Container(
                    width: 56,
                    height: 56,
                    color: AppColors.brandBrown50,
                    child: Icon(icon, size: 24),
                  ),
                ),
              )
            else
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: AppColors.brandBrown50,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Icon(icon, size: 24, color: AppColors.textMuted),
              ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    hasPhoto
                        ? 'Tap to retake'
                        : (uploading ? 'Uploading…' : 'Tap to capture / pick'),
                    style: TextStyle(
                      fontSize: 12,
                      color: hasPhoto
                          ? AppColors.success
                          : AppColors.textMuted,
                    ),
                  ),
                ],
              ),
            ),
            if (uploading)
              const SizedBox(
                width: 18,
                height: 18,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            else
              Icon(
                hasPhoto ? Icons.check_circle : icon,
                color: hasPhoto ? AppColors.success : AppColors.brandGoldDark,
              ),
          ],
        ),
      ),
    );
  }
}
