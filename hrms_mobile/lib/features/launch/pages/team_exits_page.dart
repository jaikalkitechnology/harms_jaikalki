import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../polish/widgets/asset_widgets.dart';
import '../data/exit_models.dart';
import '../data/launch_api.dart';

/// For reporting managers: team members who are leaving, and whether
/// they've handed back their company assets (asset NOC).
class TeamExitsPage extends StatefulWidget {
  const TeamExitsPage({super.key});

  @override
  State<TeamExitsPage> createState() => _TeamExitsPageState();
}

class _TeamExitsPageState extends State<TeamExitsPage> {
  late Future<List<TeamExit>> _future = sl<LaunchApi>().teamExits();

  Future<void> _refresh() async {
    setState(() => _future = sl<LaunchApi>().teamExits());
    await _future;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Team exits')),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<TeamExit>>(
          future: _future,
          builder: (context, snap) {
            if (snap.hasError) {
              return _Message('Could not load your team. Pull down to try again.');
            }
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final exits = snap.data!;
            if (exits.isEmpty) {
              return _Message('No one in your team is leaving right now.');
            }
            final pending = exits.where((e) => !e.assets.cleared).length;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Padding(
                  padding: const EdgeInsets.only(left: 4, bottom: 10),
                  child: Text(
                    pending == 0
                        ? 'All leaving team members have returned their assets.'
                        : '$pending of ${exits.length} still have company assets to return.',
                    style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
                  ),
                ),
                for (final e in exits) _ExitCard(exit: e),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _Message extends StatelessWidget {
  const _Message(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(24),
      children: [
        const SizedBox(height: 80),
        const Icon(Icons.groups_outlined, size: 56, color: AppColors.brandGoldDark),
        const SizedBox(height: 12),
        Text(text, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textMuted)),
      ],
    );
  }
}

class _ExitCard extends StatelessWidget {
  const _ExitCard({required this.exit});
  final TeamExit exit;

  @override
  Widget build(BuildContext context) {
    final e = exit;
    final lwd = e.lastWorkingDay == null ? null : DateTime.tryParse(e.lastWorkingDay!);
    final today = DateTime.now();
    final daysLeft = lwd?.difference(DateTime(today.year, today.month, today.day)).inDays;
    final when = lwd == null
        ? 'Last day not set'
        : daysLeft! > 0
            ? 'Last day ${fmtDay(e.lastWorkingDay)} · $daysLeft day${daysLeft == 1 ? '' : 's'} left'
            : daysLeft == 0
                ? 'Last day today'
                : 'Left on ${fmtDay(e.lastWorkingDay)}';
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 4, bottom: 6),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  e.employeeName,
                  style: TextStyle(
                    color: context.textPrimary,
                    fontWeight: FontWeight.w600,
                    fontSize: 16,
                  ),
                ),
                Text(
                  [e.employeeCode, e.designation, when]
                      .whereType<String>()
                      .join(' · '),
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ),
          AssetClearanceCard(clearance: e.assets),
        ],
      ),
    );
  }
}
