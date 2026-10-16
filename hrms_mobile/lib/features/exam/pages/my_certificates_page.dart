import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:share_plus/share_plus.dart';

import '../../../core/di/injection.dart';
import '../../../core/files/file_saver.dart';
import '../../../core/theme/app_colors.dart';
import '../data/exam_api.dart';
import '../data/exam_models.dart';

class MyCertificatesPage extends StatefulWidget {
  const MyCertificatesPage({super.key});

  @override
  State<MyCertificatesPage> createState() => _MyCertificatesPageState();
}

class _MyCertificatesPageState extends State<MyCertificatesPage> {
  late Future<List<CertificateOut>> _future;
  final Set<int> _busy = {};

  @override
  void initState() {
    super.initState();
    _future = sl<ExamApi>().myCertificates();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<ExamApi>().myCertificates());
    await _future;
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

  Future<void> _download(CertificateOut cert) async {
    setState(() => _busy.add(cert.id));
    try {
      final pdf = await sl<ExamApi>().certificatePdf(cert);
      final problem = await saveAndOpenBytes(
        pdf.bytes,
        filename: pdf.filename,
        mimeType: pdf.mimeType,
      );
      _toast(problem ?? 'Downloaded ${pdf.filename}', error: problem != null);
    } catch (e) {
      _toast('Download failed: $e', error: true);
    } finally {
      if (mounted) setState(() => _busy.remove(cert.id));
    }
  }

  Future<void> _share(CertificateOut cert) async {
    setState(() => _busy.add(cert.id));
    try {
      final pdf = await sl<ExamApi>().certificatePdf(cert);
      await Share.shareXFiles(
        [
          XFile.fromData(
            Uint8List.fromList(pdf.bytes),
            name: pdf.filename,
            mimeType: pdf.mimeType,
          ),
        ],
        text: 'Jaikalki Certificate · ${cert.certificateNumber}',
        subject: cert.title,
      );
    } catch (e) {
      _toast('Share failed: $e', error: true);
    } finally {
      if (mounted) setState(() => _busy.remove(cert.id));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Certificates'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _refresh),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<CertificateOut>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final certs = snap.data!;
            if (certs.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.workspace_premium,
                      size: 72, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No certificates yet.\nCertificates from HR, and for finished courses and exams, show up here.',
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: AppColors.textMuted,
                          ),
                    ),
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: certs.length,
              itemBuilder: (_, i) => _CertificateCard(
                cert: certs[i],
                busy: _busy.contains(certs[i].id),
                onDownload: () => _download(certs[i]),
                onShare: () => _share(certs[i]),
              ),
            );
          },
        ),
      ),
    );
  }
}

class _CertificateCard extends StatelessWidget {
  const _CertificateCard({
    required this.cert,
    required this.busy,
    required this.onDownload,
    required this.onShare,
  });

  final CertificateOut cert;
  final bool busy;
  final VoidCallback onDownload;
  final VoidCallback onShare;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final today = DateTime.now();
    final expired = cert.expiryDate != null &&
        DateTime.tryParse(cert.expiryDate!) != null &&
        DateTime.parse(cert.expiryDate!).isBefore(today);

    final bgGradient = cert.isRevoked
        ? const LinearGradient(
            colors: [Color(0xFFC53030), Color(0xFF8B1F1F)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          )
        : LinearGradient(
            colors: expired
                ? const [Color(0xFFE89F1A), Color(0xFFC8941A)]
                : const [Color(0xFF3D2817), Color(0xFF5C3D24)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          );

    Widget statusChip() {
      Color c;
      String label;
      if (cert.isRevoked) {
        c = Colors.red.shade100;
        label = 'REVOKED';
      } else if (expired) {
        c = Colors.amber.shade100;
        label = 'EXPIRED';
      } else {
        c = Colors.green.shade100;
        label = 'ACTIVE';
      }
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: c,
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          label,
          style: const TextStyle(
            fontSize: 10,
            fontWeight: FontWeight.bold,
            color: Color(0xFF2D1810),
          ),
        ),
      );
    }

    return GestureDetector(
      onTap: busy ? null : onDownload,
      child: Container(
        margin: const EdgeInsets.only(bottom: 16),
        decoration: BoxDecoration(
          gradient: bgGradient,
          borderRadius: BorderRadius.circular(16),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withOpacity(0.15),
              blurRadius: 14,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Decorative top — gold ribbon + medal
            Container(
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: AppColors.brandGold.withOpacity(0.5),
                    width: 1,
                  ),
                ),
              ),
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 14),
              child: Row(
                children: [
                  Container(
                    width: 44,
                    height: 44,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: AppColors.brandGold,
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.18),
                          blurRadius: 6,
                        ),
                      ],
                    ),
                    child: const Icon(
                      Icons.workspace_premium,
                      color: Color(0xFF3D2817),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          cert.headlineLabel,
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.brandGold,
                            letterSpacing: 1.4,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          'Jaikalki Technology Pvt Ltd',
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: Colors.white.withOpacity(0.85),
                          ),
                        ),
                      ],
                    ),
                  ),
                  statusChip(),
                ],
              ),
            ),
            // Body
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 18),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    cert.title,
                    style: theme.textTheme.headlineSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    cert.certificateNumber,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: AppColors.brandGoldLight,
                      fontFamily: 'JetBrainsMono',
                    ),
                  ),
                  const SizedBox(height: 14),
                  Row(
                    children: [
                      Expanded(
                        child: _InfoBlock(
                          label: 'Issued',
                          value: cert.issuedDate,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _InfoBlock(
                          label: 'Valid until',
                          value: cert.expiryDate ?? 'No expiry',
                        ),
                      ),
                      if (cert.scorePercentage != null) ...[
                        const SizedBox(width: 12),
                        Expanded(
                          child: _InfoBlock(
                            label: 'Score',
                            value: '${cert.scorePercentage!.toStringAsFixed(1)}%',
                          ),
                        ),
                      ],
                    ],
                  ),
                  if (cert.isRevoked && cert.revokedReason != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.cancel,
                              color: Colors.white70, size: 16),
                          const SizedBox(width: 6),
                          Expanded(
                            child: Text(
                              'Revoked: ${cert.revokedReason}',
                              style: theme.textTheme.bodySmall?.copyWith(
                                color: Colors.white,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 10),
                  Text(
                    'Tap card to preview · Use buttons to download / share',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.white.withOpacity(0.6),
                      fontStyle: FontStyle.italic,
                      fontSize: 11,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton.icon(
                          onPressed: busy ? null : onDownload,
                          icon: busy
                              ? const SizedBox(
                                  width: 14,
                                  height: 14,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                  ),
                                )
                              : const Icon(Icons.download),
                          label: const Text('Download'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.brandGold,
                            foregroundColor: const Color(0xFF3D2817),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      OutlinedButton.icon(
                        onPressed: busy ? null : onShare,
                        icon: const Icon(Icons.ios_share),
                        label: const Text('Share'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: Colors.white,
                          side: BorderSide(
                            color: Colors.white.withOpacity(0.6),
                          ),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoBlock extends StatelessWidget {
  const _InfoBlock({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.10),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label.toUpperCase(),
            style: theme.textTheme.labelSmall?.copyWith(
              color: AppColors.brandGoldLight,
              letterSpacing: 1.1,
              fontSize: 9,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
