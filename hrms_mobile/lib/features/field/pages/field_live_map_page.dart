import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
import '../../../core/location/location_sharing_service.dart';
import '../../../core/theme/app_colors.dart';
import '../data/field_api.dart';
import '../data/field_models.dart';

class FieldLiveMapPage extends StatefulWidget {
  const FieldLiveMapPage({super.key});

  @override
  State<FieldLiveMapPage> createState() => _FieldLiveMapPageState();
}

class _FieldLiveMapPageState extends State<FieldLiveMapPage> {
  late Future<List<LiveMapEntry>> _future;
  final _sharing = LocationSharingService.instance;

  @override
  void initState() {
    super.initState();
    _future = sl<FieldApi>().teamLiveMap();
    _sharing.addListener(_onSharingChanged);
  }

  @override
  void dispose() {
    _sharing.removeListener(_onSharingChanged);
    super.dispose();
  }

  void _onSharingChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _refresh() async {
    setState(() {
      _future = sl<FieldApi>().teamLiveMap();
    });
    await _future;
  }

  Future<void> _toggleSharing(bool on) async {
    if (on) {
      final ok = await _sharing.start();
      if (!ok && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text(
              'Location permission is required. Enable it in Settings → Apps.',
            ),
          ),
        );
      } else if (ok && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sharing your live location')),
        );
      }
    } else {
      await _sharing.stop();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Live location sharing stopped')),
        );
      }
    }
  }

  Future<void> _openMap(LiveMapEntry e) async {
    final uri = Uri.parse('https://www.google.com/maps?q=${e.lat},${e.lng}');
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'on_visit':
        return AppColors.success;
      case 'in_transit':
        return AppColors.info;
      case 'off_duty':
        return AppColors.error;
      default:
        return AppColors.brandGoldDark;
    }
  }

  String _agoFromIso(String iso) {
    final ts = DateTime.tryParse(iso);
    if (ts == null) return iso;
    final diff = DateTime.now().difference(ts);
    if (diff.inSeconds < 60) return 'Just now';
    if (diff.inMinutes < 60) return '${diff.inMinutes} min ago';
    if (diff.inHours < 24) return '${diff.inHours} h ago';
    return '${diff.inDays} d ago';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Live Team Map'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _SharingCard(
              enabled: _sharing.isEnabled,
              busy: _sharing.isBusy,
              lastSentAt: _sharing.lastSentAt,
              lastError: _sharing.lastError,
              onChanged: _toggleSharing,
            ),
            const SizedBox(height: 12),
            FutureBuilder<List<LiveMapEntry>>(
              future: _future,
              builder: (context, snap) {
                if (!snap.hasData) {
                  return const Padding(
                    padding: EdgeInsets.symmetric(vertical: 48),
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                final rows = snap.data!;
                if (rows.isEmpty) {
                  return Padding(
                    padding: const EdgeInsets.symmetric(vertical: 48),
                    child: Column(
                      children: [
                        Icon(Icons.map_outlined,
                            size: 64, color: AppColors.brandGoldDark),
                        const SizedBox(height: 16),
                        Text(
                          'No location updates yet today.',
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: AppColors.textMuted,
                          ),
                        ),
                      ],
                    ),
                  );
                }
                return Column(
                  children: [
                    for (final e in rows) ...[
                      Card(
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor:
                                _statusColor(e.currentStatus).withOpacity(0.15),
                            child: Icon(Icons.person,
                                color: _statusColor(e.currentStatus)),
                          ),
                          title: Text(e.name),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '${e.employeeCode} · ${e.currentStatus.replaceAll('_', ' ')}',
                                style: theme.textTheme.bodySmall,
                              ),
                              Text(
                                _agoFromIso(e.timestamp),
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: AppColors.textMuted,
                                ),
                              ),
                            ],
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              if (e.batteryPct != null)
                                Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(
                                      e.batteryPct! < 20
                                          ? Icons.battery_alert
                                          : Icons.battery_full,
                                      size: 16,
                                      color: e.batteryPct! < 20
                                          ? AppColors.error
                                          : AppColors.success,
                                    ),
                                    const SizedBox(width: 2),
                                    Text('${e.batteryPct}%'),
                                  ],
                                ),
                              const Icon(Icons.open_in_new, size: 16),
                            ],
                          ),
                          onTap: () => _openMap(e),
                        ),
                      ),
                      const SizedBox(height: 8),
                    ],
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _SharingCard extends StatelessWidget {
  const _SharingCard({
    required this.enabled,
    required this.busy,
    required this.lastSentAt,
    required this.lastError,
    required this.onChanged,
  });

  final bool enabled;
  final bool busy;
  final DateTime? lastSentAt;
  final String? lastError;
  final ValueChanged<bool> onChanged;

  String _ago(DateTime ts) {
    final d = DateTime.now().difference(ts);
    if (d.inSeconds < 60) return 'just now';
    if (d.inMinutes < 60) return '${d.inMinutes} min ago';
    return '${d.inHours} h ago';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: enabled ? AppColors.success.withOpacity(0.08) : null,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(
              enabled ? Icons.gps_fixed : Icons.gps_off,
              color: enabled ? AppColors.success : AppColors.textMuted,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    enabled ? 'Sharing live location' : 'Live sharing off',
                    style: theme.textTheme.titleMedium,
                  ),
                  const SizedBox(height: 2),
                  if (enabled && lastSentAt != null)
                    Text(
                      busy
                          ? 'Sending update…'
                          : 'Last update ${_ago(lastSentAt!)}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.textMuted,
                      ),
                    )
                  else if (lastError != null)
                    Text(
                      lastError!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.error,
                      ),
                    )
                  else
                    Text(
                      'Turn on to let HR / your manager see your live location.',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: AppColors.textMuted,
                      ),
                    ),
                ],
              ),
            ),
            Switch(value: enabled, onChanged: onChanged),
          ],
        ),
      ),
    );
  }
}
