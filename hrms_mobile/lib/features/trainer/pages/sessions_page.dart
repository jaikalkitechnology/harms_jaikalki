import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/trainer_api.dart';
import '../data/trainer_models.dart';

class TrainerSessionsPage extends StatefulWidget {
  const TrainerSessionsPage({super.key});

  @override
  State<TrainerSessionsPage> createState() => _TrainerSessionsPageState();
}

class _TrainerSessionsPageState extends State<TrainerSessionsPage> {
  late Future<({List<TrainingSession> upcoming, List<TrainingSession> mine})>
      _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({List<TrainingSession> upcoming, List<TrainingSession> mine})> _load() async {
    final api = sl<TrainerApi>();
    final upcoming = await api.upcomingSessions();
    final mine = await api.mySessions();
    return (upcoming: upcoming, mine: mine);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
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

  Future<void> _register(TrainingSession s) async {
    setState(() => _busy = true);
    try {
      await sl<TrainerApi>().register(s.id);
      _toast('Registered for ${s.title}');
      await _refresh();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Could not register')
          : 'Could not register';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _checkInPrompt() async {
    final ctrl = TextEditingController();
    final token = await showDialog<String>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Enter QR token'),
        content: TextField(
          controller: ctrl,
          decoration: const InputDecoration(
            hintText: 'Paste or scan the session QR token',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context, ctrl.text.trim()),
            child: const Text('Check in'),
          ),
        ],
      ),
    );
    if (token == null || token.isEmpty) return;
    setState(() => _busy = true);
    try {
      final p = await sl<TrainerApi>().checkIn(token);
      _toast('Checked in (${p.status})');
      await _refresh();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Check-in failed')
          : 'Check-in failed';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _open(String url) async {
    final uri = Uri.parse(url);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'completed':
        return AppColors.success;
      case 'in_progress':
        return AppColors.warning;
      case 'cancelled':
        return AppColors.error;
      default:
        return AppColors.info;
    }
  }

  Widget _sessionCard(TrainingSession s, {bool registered = false}) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    s.title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _statusColor(s.status).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    s.status.replaceAll('_', ' ').toUpperCase(),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: _statusColor(s.status),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            Text(s.code,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      fontFamily: 'monospace',
                      color: AppColors.brandBrownLight,
                    )),
            const SizedBox(height: 6),
            Text('${s.scheduledStart} → ${s.scheduledEnd}',
                style: Theme.of(context).textTheme.bodySmall),
            const SizedBox(height: 4),
            Text(
              '${s.participantsCount}/${s.capacity} registered · ${s.sessionType}',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    color: AppColors.brandBrownLight,
                  ),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                if (s.meetingUrl != null)
                  OutlinedButton.icon(
                    icon: const Icon(Icons.video_camera_front_outlined,
                        size: 16),
                    label: const Text('Join'),
                    onPressed: () => _open(s.meetingUrl!),
                  ),
                if (!registered &&
                    (s.status == 'open_for_registration' ||
                        s.status == 'scheduled'))
                  ElevatedButton.icon(
                    icon: const Icon(Icons.app_registration, size: 16),
                    label: const Text('Register'),
                    onPressed: _busy ? null : () => _register(s),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Training Sessions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner_outlined),
            tooltip: 'Check in with QR',
            onPressed: _checkInPrompt,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<
            ({List<TrainingSession> upcoming, List<TrainingSession> mine})>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final mineIds = snap.data!.mine.map((s) => s.id).toSet();
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (snap.data!.mine.isNotEmpty) ...[
                  Text('★ MY SESSIONS (${snap.data!.mine.length})',
                      style: theme.textTheme.labelSmall?.copyWith(
                        color: AppColors.brandGoldDark,
                      )),
                  const SizedBox(height: 8),
                  ...snap.data!.mine.map(
                    (s) => _sessionCard(s, registered: true),
                  ),
                  const SizedBox(height: 12),
                ],
                Text('★ UPCOMING (${snap.data!.upcoming.length})',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                if (snap.data!.upcoming.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(20),
                      child: Center(child: Text('No upcoming sessions')),
                    ),
                  ),
                ...snap.data!.upcoming.map(
                  (s) => _sessionCard(
                    s,
                    registered: mineIds.contains(s.id),
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}
