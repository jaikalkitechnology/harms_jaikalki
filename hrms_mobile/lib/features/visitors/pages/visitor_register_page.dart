import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../polish/data/polish_api.dart';

class VisitorRegisterPage extends StatefulWidget {
  const VisitorRegisterPage({super.key});

  @override
  State<VisitorRegisterPage> createState() => _VisitorRegisterPageState();
}

class _VisitorRegisterPageState extends State<VisitorRegisterPage> {
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _email = TextEditingController();
  final _company = TextEditingController();
  final _purpose = TextEditingController();
  DateTime _expected = DateTime.now().add(const Duration(hours: 1));
  bool _busy = false;

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    _email.dispose();
    _company.dispose();
    _purpose.dispose();
    super.dispose();
  }

  Future<void> _pickDateTime() async {
    final date = await showDatePicker(
      context: context,
      initialDate: _expected,
      firstDate: DateTime.now().subtract(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (date == null) return;
    if (!mounted) return;
    final time = await showTimePicker(
      context: context,
      initialTime: TimeOfDay.fromDateTime(_expected),
    );
    if (time == null) return;
    setState(() {
      _expected = DateTime(
        date.year,
        date.month,
        date.day,
        time.hour,
        time.minute,
      );
    });
  }

  Future<void> _submit() async {
    if (_name.text.trim().isEmpty || _purpose.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Name and purpose are required')),
      );
      return;
    }
    setState(() => _busy = true);
    try {
      final visitor = await sl<PolishApi>().preRegisterVisitor(
        fullName: _name.text.trim(),
        purpose: _purpose.text.trim(),
        expectedAt: _expected.toIso8601String(),
        company: _company.text.trim().isEmpty ? null : _company.text.trim(),
        contactPhone: _phone.text.trim().isEmpty ? null : _phone.text.trim(),
        contactEmail: _email.text.trim().isEmpty ? null : _email.text.trim(),
      );
      if (!mounted) return;
      context.pushReplacement('/visitors/pass/${visitor.id}', extra: visitor);
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Could not register')
          : 'Could not register';
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Register Visitor')),
      body: AbsorbPointer(
        absorbing: _busy,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            TextField(
              controller: _name,
              decoration: const InputDecoration(labelText: 'Full name *'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _company,
              decoration: const InputDecoration(labelText: 'Company'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _phone,
              keyboardType: TextInputType.phone,
              decoration: const InputDecoration(labelText: 'Phone'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _email,
              keyboardType: TextInputType.emailAddress,
              decoration: const InputDecoration(labelText: 'Email'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _purpose,
              decoration: const InputDecoration(
                labelText: 'Purpose of visit *',
                hintText: 'e.g. Interview, demo, meeting…',
              ),
            ),
            const SizedBox(height: 12),
            ListTile(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: BorderSide(color: Colors.black.withOpacity(0.15)),
              ),
              leading: const Icon(Icons.event),
              title: const Text('Expected at'),
              subtitle: Text(_expected.toString()),
              trailing: const Icon(Icons.chevron_right),
              onTap: _pickDateTime,
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: _busy
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.qr_code_2),
              label: const Text('Generate QR pass'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.brandGoldDark,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
              onPressed: _busy ? null : _submit,
            ),
          ],
        ),
      ),
    );
  }
}
