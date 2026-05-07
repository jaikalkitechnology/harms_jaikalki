import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/sales_api.dart';
import '../data/sales_models.dart';

const _stageColor = <String, Color>{
  'new': AppColors.info,
  'contacted': AppColors.brandGoldDark,
  'qualified': AppColors.brandGoldDark,
  'proposal': AppColors.warning,
  'negotiation': AppColors.warning,
  'won': AppColors.success,
  'lost': AppColors.error,
};

class MyLeadsPage extends StatefulWidget {
  const MyLeadsPage({super.key});

  @override
  State<MyLeadsPage> createState() => _MyLeadsPageState();
}

class _MyLeadsPageState extends State<MyLeadsPage> {
  late Future<List<Lead>> _future;
  String? _stage;

  @override
  void initState() {
    super.initState();
    _load();
  }

  void _load() {
    _future = sl<SalesApi>().myLeads(stage: _stage);
  }

  Future<void> _refresh() async {
    setState(_load);
    await _future;
  }

  String _inr(double v) {
    return '₹${v.toStringAsFixed(0)}';
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Leads'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refresh,
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          final created = await context.push<bool>('/sales/leads/new');
          if (created == true) _refresh();
        },
        icon: const Icon(Icons.add),
        label: const Text('New lead'),
      ),
      body: Column(
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                _stageChip(null, 'All'),
                ..._stageColor.keys.map(_stageChip),
              ],
            ),
          ),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _refresh,
              child: FutureBuilder<List<Lead>>(
                future: _future,
                builder: (context, snap) {
                  if (!snap.hasData) {
                    return const Center(child: CircularProgressIndicator());
                  }
                  final leads = snap.data!;
                  if (leads.isEmpty) {
                    return ListView(
                      children: [
                        const SizedBox(height: 80),
                        Icon(Icons.handshake_outlined,
                            size: 64, color: AppColors.brandGoldDark),
                        const SizedBox(height: 12),
                        Text(
                          'No leads ${_stage != null ? "in $_stage" : "yet"}.',
                          textAlign: TextAlign.center,
                          style: theme.textTheme.bodyMedium?.copyWith(
                            color: AppColors.brandBrownLight,
                          ),
                        ),
                      ],
                    );
                  }
                  return ListView.separated(
                    padding: const EdgeInsets.all(12),
                    itemCount: leads.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, i) {
                      final l = leads[i];
                      final color = _stageColor[l.stage] ?? AppColors.brandGoldDark;
                      return Card(
                        child: InkWell(
                          borderRadius: BorderRadius.circular(12),
                          onTap: () async {
                            await context.push('/sales/leads/${l.id}');
                            _refresh();
                          },
                          child: Padding(
                            padding: const EdgeInsets.all(14),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        l.contactName ?? 'Lead #${l.id}',
                                        style: theme.textTheme.titleMedium,
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 4,
                                      ),
                                      decoration: BoxDecoration(
                                        color: color.withOpacity(0.15),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        l.stage,
                                        style: theme.textTheme.labelSmall
                                            ?.copyWith(color: color),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                if (l.contactPhone != null ||
                                    l.contactEmail != null)
                                  Text(
                                    [l.contactPhone, l.contactEmail]
                                        .whereType<String>()
                                        .join(' · '),
                                    style: theme.textTheme.bodySmall?.copyWith(
                                      color: AppColors.brandBrownLight,
                                    ),
                                  ),
                                const SizedBox(height: 6),
                                Row(
                                  children: [
                                    Icon(Icons.currency_rupee,
                                        size: 14,
                                        color: AppColors.brandGoldDark),
                                    Text(_inr(l.expectedValue)),
                                    const SizedBox(width: 12),
                                    Icon(Icons.source,
                                        size: 14,
                                        color: AppColors.brandBrownLight),
                                    const SizedBox(width: 4),
                                    Text(l.source.replaceAll('_', ' ')),
                                    const Spacer(),
                                    Icon(Icons.bolt,
                                        size: 14,
                                        color: AppColors.brandBrownLight),
                                    const SizedBox(width: 2),
                                    Text('${l.score}'),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _stageChip(String? stage, [String? label]) {
    final selected = stage == _stage;
    final color =
        stage == null ? AppColors.brandGoldDark : (_stageColor[stage] ?? AppColors.brandGoldDark);
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: ChoiceChip(
        label: Text(label ?? stage!),
        selected: selected,
        onSelected: (_) {
          setState(() {
            _stage = stage;
            _load();
          });
        },
        selectedColor: color.withOpacity(0.15),
        labelStyle: TextStyle(
          color: selected ? color : AppColors.brandBrownDarker,
        ),
      ),
    );
  }
}
