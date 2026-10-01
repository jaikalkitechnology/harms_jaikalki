import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/launch_api.dart';

class MfaSetupPage extends StatefulWidget {
  const MfaSetupPage({super.key});

  @override
  State<MfaSetupPage> createState() => _MfaSetupPageState();
}

class _MfaSetupPageState extends State<MfaSetupPage> {
  MfaEnrollResponse? _enroll;
  final _codeCtrl = TextEditingController();
  List<String>? _backupCodes;
  bool _busy = false;

  @override
  void dispose() {
    _codeCtrl.dispose();
    super.dispose();
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

  Future<void> _start() async {
    setState(() => _busy = true);
    try {
      final r = await sl<LaunchApi>().mfaEnroll();
      setState(() => _enroll = r);
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Failed')
          : 'Failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _verify() async {
    if (_codeCtrl.text.length < 6) {
      _toast('Enter the 6-digit code', error: true);
      return;
    }
    setState(() => _busy = true);
    try {
      final codes = await sl<LaunchApi>().mfaVerify(_codeCtrl.text.trim());
      setState(() => _backupCodes = codes);
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Failed')
          : 'Failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Enable MFA')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_backupCodes != null) ...[
              Card(
                color: AppColors.brandGoldPale,
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('★ MFA ENABLED',
                          style: theme.textTheme.labelSmall?.copyWith(
                            color: AppColors.brandGoldDark,
                          )),
                      const SizedBox(height: 8),
                      Text(
                        'Save these backup codes somewhere safe — each one '
                        'works once if you lose your phone.',
                        style: theme.textTheme.bodyMedium,
                      ),
                      const SizedBox(height: 12),
                      ..._backupCodes!.map(
                        (c) => Container(
                          margin: const EdgeInsets.symmetric(vertical: 2),
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: SelectableText(
                            c,
                            style: const TextStyle(
                              fontFamily: 'JetBrainsMono',
                              letterSpacing: 1.5,
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 12),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.copy),
                        label: const Text('Copy all'),
                        onPressed: () {
                          Clipboard.setData(
                            ClipboardData(text: _backupCodes!.join('\n')),
                          );
                          _toast('Backup codes copied');
                        },
                      ),
                    ],
                  ),
                ),
              ),
            ] else if (_enroll != null) ...[
              Text('Step 2 — Verify',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: AppColors.brandGoldDark,
                  )),
              const SizedBox(height: 8),
              Text(
                'Open Google Authenticator (or any TOTP app), tap +, choose '
                '"Enter a setup key", and paste the secret below. Then enter '
                'the current 6-digit code.',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              SelectableText(
                _enroll!.secret,
                style: const TextStyle(
                  fontFamily: 'JetBrainsMono',
                  fontSize: 18,
                  letterSpacing: 2,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Center(
                child: TextButton.icon(
                  icon: const Icon(Icons.copy, size: 14),
                  label: const Text('Copy secret'),
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: _enroll!.secret));
                    _toast('Secret copied');
                  },
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _codeCtrl,
                keyboardType: TextInputType.number,
                maxLength: 6,
                decoration: const InputDecoration(
                  labelText: '6-digit code',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: _busy ? null : _verify,
                child: const Text('Verify & enable'),
              ),
            ] else ...[
              Text('Step 1 — Start MFA enrollment',
                  style: theme.textTheme.labelSmall?.copyWith(
                    color: AppColors.brandGoldDark,
                  )),
              const SizedBox(height: 8),
              Text(
                'Two-factor authentication adds a 6-digit code from an '
                'authenticator app on top of your password. Strongly '
                'recommended for HR and admin accounts.',
                style: theme.textTheme.bodyMedium,
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                icon: const Icon(Icons.lock_outline),
                label: const Text('Generate my secret'),
                onPressed: _busy ? null : _start,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
