import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:mobile_scanner/mobile_scanner.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../polish/data/polish_api.dart';
import '../../polish/data/polish_models.dart';

class VisitorScanPage extends StatefulWidget {
  const VisitorScanPage({super.key});

  @override
  State<VisitorScanPage> createState() => _VisitorScanPageState();
}

class _VisitorScanPageState extends State<VisitorScanPage> {
  final MobileScannerController _controller = MobileScannerController(
    detectionSpeed: DetectionSpeed.normal,
    facing: CameraFacing.back,
  );
  bool _busy = false;
  Visitor? _scanned;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _onDetect(BarcodeCapture capture) async {
    if (_busy || _scanned != null) return;
    final raw = capture.barcodes.firstOrNull?.rawValue;
    if (raw == null || raw.isEmpty) return;
    setState(() => _busy = true);
    try {
      final v = await sl<PolishApi>().visitorByToken(raw);
      if (!mounted) return;
      setState(() => _scanned = v);
      await _controller.stop();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Invalid QR')
          : 'Invalid QR';
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(msg)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _action(String action) async {
    if (_scanned == null) return;
    setState(() => _busy = true);
    try {
      Visitor updated;
      if (action == 'check_in') {
        updated =
            await sl<PolishApi>().checkInVisitor(_scanned!.qrToken);
      } else {
        updated =
            await sl<PolishApi>().checkOutVisitorByToken(_scanned!.qrToken);
      }
      if (!mounted) return;
      setState(() => _scanned = updated);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            action == 'check_in'
                ? 'Checked in ${updated.fullName}'
                : 'Checked out ${updated.fullName}',
          ),
          backgroundColor: AppColors.success,
        ),
      );
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Failed')
          : 'Failed';
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(msg)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _scanAgain() async {
    setState(() => _scanned = null);
    await _controller.start();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan Visitor QR'),
        actions: [
          IconButton(
            icon: const Icon(Icons.flash_on),
            onPressed: () => _controller.toggleTorch(),
          ),
          IconButton(
            icon: const Icon(Icons.cameraswitch),
            onPressed: () => _controller.switchCamera(),
          ),
        ],
      ),
      body: _scanned == null
          ? _buildScanner()
          : _buildPreview(_scanned!),
    );
  }

  Widget _buildScanner() {
    return Stack(
      children: [
        MobileScanner(
          controller: _controller,
          onDetect: _onDetect,
        ),
        Center(
          child: Container(
            width: 240,
            height: 240,
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.brandGold, width: 3),
              borderRadius: BorderRadius.circular(16),
            ),
          ),
        ),
        if (_busy)
          const Positioned.fill(
            child: ColoredBox(
              color: Colors.black54,
              child: Center(child: CircularProgressIndicator()),
            ),
          ),
        Positioned(
          bottom: 24,
          left: 16,
          right: 16,
          child: Card(
            color: Colors.black54,
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: Row(
                children: const [
                  Icon(Icons.qr_code_scanner, color: Colors.white),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Align the visitor QR inside the frame.',
                      style: TextStyle(color: Colors.white),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildPreview(Visitor v) {
    final theme = Theme.of(context);
    final canCheckIn =
        v.status == 'scheduled' || v.status == 'checked_in';
    final canCheckOut = v.status == 'checked_in';
    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(v.fullName, style: theme.textTheme.titleLarge),
                  if (v.company != null)
                    Text(v.company!,
                        style: theme.textTheme.bodySmall?.copyWith(
                          color: AppColors.brandBrownLight,
                        )),
                  const SizedBox(height: 8),
                  Text('Purpose: ${v.purpose}'),
                  Text('Expected: ${v.expectedAt}'),
                  if (v.contactPhone != null) Text('Phone: ${v.contactPhone}'),
                  if (v.badgeNumber != null) Text('Badge: ${v.badgeNumber}'),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.brandGoldPale,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Text(
                      v.status.replaceAll('_', ' ').toUpperCase(),
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (canCheckIn)
            ElevatedButton.icon(
              icon: const Icon(Icons.login),
              label: const Text('Check in'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.success,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: _busy ? null : () => _action('check_in'),
            ),
          if (canCheckOut) ...[
            const SizedBox(height: 8),
            OutlinedButton.icon(
              icon: const Icon(Icons.logout),
              label: const Text('Check out'),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: _busy ? null : () => _action('check_out'),
            ),
          ],
          const SizedBox(height: 12),
          TextButton.icon(
            icon: const Icon(Icons.qr_code_scanner_outlined),
            label: const Text('Scan another'),
            onPressed: _busy ? null : _scanAgain,
          ),
        ],
      ),
    );
  }
}

extension _BarcodeFirstOrNull on List<Barcode> {
  Barcode? get firstOrNull => isEmpty ? null : first;
}
