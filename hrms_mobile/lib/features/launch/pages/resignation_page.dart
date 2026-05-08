import 'package:dio/dio.dart';
import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/launch_api.dart';

class ResignationPage extends StatefulWidget {
  const ResignationPage({super.key});

  @override
  State<ResignationPage> createState() => _ResignationPageState();
}

class _ResignationPageState extends State<ResignationPage> {
  late Future<_State> _future;
  final _reasonCtrl = TextEditingController();
  DateTime _proposed = DateTime.now().add(const Duration(days: 60));
  int _notice = 60;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  @override
  void dispose() {
    _reasonCtrl.dispose();
    super.dispose();
  }

  Future<_State> _load() async {
    final api = sl<LaunchApi>();
    final status = await api.resignationUnlockStatus();
    final mine = await api.myResignations();
    return _State(
      unlocked: status['unlocked'] == true,
      hasOpenRequest: status['has_open_request'] == true,
      requests: mine,
    );
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _proposed,
      firstDate: DateTime.now().add(const Duration(days: 1)),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );
    if (picked != null) {
      setState(() => _proposed = picked);
    }
  }

  Future<void> _submit() async {
    setState(() => _busy = true);
    try {
      await sl<LaunchApi>().submitResignation(
        proposedLastWorkingDay: _proposed.toIso8601String().split('T').first,
        reason: _reasonCtrl.text.trim().isEmpty
            ? null
            : _reasonCtrl.text.trim(),
        noticePeriodDays: _notice,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Resignation submitted to your manager'),
          backgroundColor: AppColors.success,
        ),
      );
      _reasonCtrl.clear();
      await _refresh();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Submit failed')
          : 'Submit failed';
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(msg)),
        );
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Resignation')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<_State>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final s = snap.data!;
            if (!s.unlocked) {
              return _buildLocked(s);
            }
            if (s.hasOpenRequest) {
              return _buildAlreadyOpen(s);
            }
            return _buildForm();
          },
        ),
      ),
    );
  }

  Widget _buildLocked(_State s) {
    final theme = Theme.of(context);
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const SizedBox(height: 40),
        Center(
          child: Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.brandGoldPale,
            ),
            child: Icon(
              Icons.lock_outline,
              size: 56,
              color: AppColors.brandGoldDark,
            ),
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'Resignation submission is locked',
          textAlign: TextAlign.center,
          style: theme.textTheme.headlineSmall?.copyWith(
            color: AppColors.brandBrownDarker,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          'For policy reasons, you cannot file a resignation directly from '
          'the app.\n\nIf you have already discussed your decision with your '
          'manager and HR (e.g. via email), please request HR / admin to '
          'unlock this option for you. Once unlocked, you can submit your '
          'resignation here.',
          textAlign: TextAlign.center,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: AppColors.brandBrownLight,
            height: 1.5,
          ),
        ),
        const SizedBox(height: 24),
        if (s.requests.isNotEmpty) ...[
          Text(
            'Past requests',
            style: theme.textTheme.labelSmall?.copyWith(
              color: AppColors.brandGoldDark,
              letterSpacing: 1.4,
            ),
          ),
          const SizedBox(height: 8),
          ..._historyTiles(s.requests),
        ],
        const SizedBox(height: 24),
        OutlinedButton.icon(
          icon: const Icon(Icons.refresh),
          label: const Text('Check again'),
          onPressed: _refresh,
        ),
      ],
    );
  }

  Widget _buildAlreadyOpen(_State s) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        const SizedBox(height: 20),
        Card(
          color: AppColors.brandGoldPale,
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Row(
              children: [
                Icon(Icons.hourglass_top,
                    color: AppColors.brandGoldDark, size: 32),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    'You already have an active resignation request. '
                    'Track its progress below.',
                    style: TextStyle(color: AppColors.brandBrownDarker),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        ..._historyTiles(s.requests),
      ],
    );
  }

  Widget _buildForm() {
    final theme = Theme.of(context);
    return AbsorbPointer(
      absorbing: _busy,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Card(
            color: AppColors.success.withOpacity(0.10),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Icon(Icons.lock_open, color: AppColors.success),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Resignation is unlocked. You can submit your request '
                      'now. After submission, the lock automatically resets.',
                      style: theme.textTheme.bodySmall,
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          ListTile(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: BorderSide(color: Colors.black.withOpacity(0.15)),
            ),
            leading: const Icon(Icons.event),
            title: const Text('Proposed last working day'),
            subtitle: Text(_proposed.toString().split(' ').first),
            trailing: const Icon(Icons.chevron_right),
            onTap: _pickDate,
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<int>(
            decoration: const InputDecoration(
              labelText: 'Notice period (days)',
              border: OutlineInputBorder(),
            ),
            value: _notice,
            items: const [
              DropdownMenuItem(value: 30, child: Text('30 days')),
              DropdownMenuItem(value: 60, child: Text('60 days')),
              DropdownMenuItem(value: 90, child: Text('90 days')),
            ],
            onChanged: (v) {
              if (v != null) setState(() => _notice = v);
            },
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _reasonCtrl,
            maxLines: 4,
            decoration: const InputDecoration(
              labelText: 'Reason (optional)',
              border: OutlineInputBorder(),
              hintText: 'Share your reason for resigning…',
            ),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            icon: _busy
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send),
            label: const Text('Submit resignation'),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.brandGoldDark,
              foregroundColor: Colors.white,
              padding: const EdgeInsets.symmetric(vertical: 14),
            ),
            onPressed: _busy ? null : _submit,
          ),
        ],
      ),
    );
  }

  List<Widget> _historyTiles(List<dynamic> rows) {
    return rows.map((raw) {
      final r = raw as Map<String, dynamic>;
      final status = (r['status'] as String?) ?? 'unknown';
      final lwd = (r['proposed_last_working_day'] as String?) ?? '—';
      final reason = (r['reason'] as String?) ?? '';
      return Card(
        margin: const EdgeInsets.only(bottom: 8),
        child: ListTile(
          leading: const Icon(Icons.assignment_outlined),
          title: Text('LWD $lwd'),
          subtitle: Text('${status.replaceAll('_', ' ')}  $reason'),
        ),
      );
    }).toList();
  }
}

class _State {
  _State({
    required this.unlocked,
    required this.hasOpenRequest,
    required this.requests,
  });
  final bool unlocked;
  final bool hasOpenRequest;
  final List<dynamic> requests;
}
