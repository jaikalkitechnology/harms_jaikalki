import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
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

  @override
  void initState() {
    super.initState();
    _future = sl<FieldApi>().teamLiveMap();
  }

  Future<void> _refresh() async {
    setState(() {
      _future = sl<FieldApi>().teamLiveMap();
    });
    await _future;
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
        child: FutureBuilder<List<LiveMapEntry>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final rows = snap.data!;
            if (rows.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 80),
                  Icon(Icons.map_outlined,
                      size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Text(
                    'No location updates yet today.',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: AppColors.brandBrownLight,
                    ),
                  ),
                ],
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: rows.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, i) {
                final e = rows[i];
                return Card(
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
                            color: AppColors.brandBrownLight,
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
                );
              },
            );
          },
        ),
      ),
    );
  }
}
