import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/trainer_api.dart';
import '../data/trainer_models.dart';

class TrainerMarketplacePage extends StatefulWidget {
  const TrainerMarketplacePage({super.key});

  @override
  State<TrainerMarketplacePage> createState() => _TrainerMarketplacePageState();
}

class _TrainerMarketplacePageState extends State<TrainerMarketplacePage> {
  late Future<List<Trainer>> _future;
  String _search = '';

  @override
  void initState() {
    super.initState();
    _future = sl<TrainerApi>().trainers();
  }

  void _runSearch(String q) {
    setState(() {
      _search = q;
      _future = sl<TrainerApi>().trainers(
        search: q.isEmpty ? null : q,
      );
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Trainers')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Search by name or specialization',
                border: OutlineInputBorder(),
              ),
              onSubmitted: _runSearch,
              onChanged: (v) {
                if (v.isEmpty && _search.isNotEmpty) _runSearch('');
              },
            ),
          ),
          Expanded(
            child: FutureBuilder<List<Trainer>>(
              future: _future,
              builder: (context, snap) {
                if (!snap.hasData) {
                  return const Center(child: CircularProgressIndicator());
                }
                final trainers = snap.data!;
                if (trainers.isEmpty) {
                  return Center(
                    child: Text(
                      'No trainers found.',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: AppColors.brandBrownLight,
                      ),
                    ),
                  );
                }
                return ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: trainers.length,
                  itemBuilder: (context, i) {
                    final t = trainers[i];
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                CircleAvatar(
                                  backgroundColor: AppColors.brandGoldPale,
                                  child: Text(
                                    t.fullName.isNotEmpty
                                        ? t.fullName[0]
                                        : '?',
                                    style: TextStyle(
                                      color: AppColors.brandGoldDark,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        t.fullName,
                                        style: theme.textTheme.titleMedium,
                                      ),
                                      if (t.headline != null)
                                        Text(
                                          t.headline!,
                                          style: theme.textTheme.bodySmall
                                              ?.copyWith(
                                            color: AppColors.brandBrownLight,
                                          ),
                                        ),
                                    ],
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: t.isExternal
                                        ? AppColors.info.withOpacity(0.15)
                                        : AppColors.brandGoldDark
                                            .withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text(
                                    t.isExternal ? 'EXTERNAL' : 'INTERNAL',
                                    style: TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.bold,
                                      color: t.isExternal
                                          ? AppColors.info
                                          : AppColors.brandGoldDark,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 12),
                            Row(
                              children: [
                                Icon(Icons.star,
                                    size: 14, color: AppColors.brandGoldDark),
                                const SizedBox(width: 4),
                                Text(t.ratingAverage.toStringAsFixed(1),
                                    style: theme.textTheme.bodySmall),
                                const SizedBox(width: 12),
                                Icon(Icons.work_outline,
                                    size: 14,
                                    color: AppColors.brandBrownLight),
                                const SizedBox(width: 4),
                                Text('${t.sessionsCompleted} sessions',
                                    style: theme.textTheme.bodySmall),
                                const SizedBox(width: 12),
                                Text('${t.yearsExperience}y exp',
                                    style: theme.textTheme.bodySmall),
                              ],
                            ),
                            if (t.specializations != null &&
                                t.specializations!.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              Wrap(
                                spacing: 6,
                                runSpacing: 6,
                                children: t.specializations!
                                    .map(
                                      (s) => Container(
                                        padding: const EdgeInsets.symmetric(
                                            horizontal: 8, vertical: 2),
                                        decoration: BoxDecoration(
                                          color: AppColors.brandBrown50,
                                          borderRadius:
                                              BorderRadius.circular(6),
                                        ),
                                        child: Text(
                                          s,
                                          style: const TextStyle(fontSize: 11),
                                        ),
                                      ),
                                    )
                                    .toList(),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
