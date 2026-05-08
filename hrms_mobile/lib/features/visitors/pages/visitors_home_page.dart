import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../polish/data/polish_api.dart';
import '../../polish/data/polish_models.dart';

class VisitorsHomePage extends StatefulWidget {
  const VisitorsHomePage({super.key});

  @override
  State<VisitorsHomePage> createState() => _VisitorsHomePageState();
}

class _VisitorsHomePageState extends State<VisitorsHomePage> {
  late Future<List<Visitor>> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<PolishApi>().myVisitors();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<PolishApi>().myVisitors());
    await _future;
  }

  Color _statusColor(String s) {
    switch (s) {
      case 'checked_in':
        return AppColors.success;
      case 'checked_out':
        return AppColors.brandBrownLight;
      case 'cancelled':
      case 'no_show':
        return AppColors.error;
      default:
        return AppColors.info;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Visitors'),
        actions: [
          IconButton(
            icon: const Icon(Icons.qr_code_scanner_outlined),
            tooltip: 'Scan visitor QR',
            onPressed: () => context.push(AppRoutes.visitorScan),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await context.push(AppRoutes.visitorRegister);
          if (created == true) await _refresh();
        },
        icon: const Icon(Icons.person_add_alt_1),
        label: const Text('Register'),
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<Visitor>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final list = snap.data!;
            if (list.isEmpty) {
              return ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  const SizedBox(height: 60),
                  Icon(Icons.qr_code, size: 64, color: AppColors.brandGoldDark),
                  const SizedBox(height: 16),
                  Center(
                    child: Text(
                      'No visitors registered yet.\nTap "Register" to create a QR pass.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  ),
                ],
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: list.length,
              itemBuilder: (_, i) {
                final v = list[i];
                final color = _statusColor(v.status);
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: color.withOpacity(0.18),
                      child: Icon(Icons.qr_code_2, color: color),
                    ),
                    title: Text(v.fullName),
                    subtitle: Text(
                      '${v.purpose}\n${v.expectedAt}',
                      style: theme.textTheme.bodySmall,
                    ),
                    isThreeLine: true,
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: color.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        v.status.replaceAll('_', ' ').toUpperCase(),
                        style: TextStyle(
                          fontSize: 10,
                          color: color,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    onTap: () => context.push(
                      '${AppRoutes.visitorPass}/${v.id}',
                      extra: v,
                    ),
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
