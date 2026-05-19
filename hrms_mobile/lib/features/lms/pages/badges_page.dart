import 'package:flutter/material.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/lms_api.dart';
import '../data/lms_models.dart';

class BadgesPage extends StatefulWidget {
  const BadgesPage({super.key});

  @override
  State<BadgesPage> createState() => _BadgesPageState();
}

class _BadgesPageState extends State<BadgesPage> {
  late Future<LearningStats> _future;

  @override
  void initState() {
    super.initState();
    _future = sl<LmsApi>().myStats();
  }

  Color _tierColor(String tier) {
    switch (tier) {
      case 'platinum':
        return AppColors.info;
      case 'gold':
        return AppColors.brandGoldDark;
      case 'silver':
        return const Color(0xFFB6BCC4);
      default:
        return AppColors.warning;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('My Badges')),
      body: FutureBuilder<LearningStats>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final stats = snap.data!;
          if (stats.badges.isEmpty) {
            return Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.emoji_events_outlined,
                        size: 64, color: AppColors.brandGoldDark),
                    const SizedBox(height: 16),
                    Text(
                      'No badges yet.\nComplete a lesson to earn your first one.',
                      textAlign: TextAlign.center,
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: context.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
            );
          }
          return GridView.builder(
            padding: const EdgeInsets.all(16),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 1,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
            ),
            itemCount: stats.badges.length,
            itemBuilder: (context, i) {
              final b = stats.badges[i];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        b.icon ?? '🏅',
                        style: const TextStyle(fontSize: 48),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        b.name,
                        style: theme.textTheme.titleSmall,
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 8, vertical: 2),
                        decoration: BoxDecoration(
                          color: _tierColor(b.tier),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          b.tier.toUpperCase(),
                          style: const TextStyle(
                            fontSize: 10,
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      if (b.description != null) ...[
                        const SizedBox(height: 4),
                        Text(
                          b.description!,
                          style: theme.textTheme.bodySmall?.copyWith(
                            color: context.textMuted,
                          ),
                          textAlign: TextAlign.center,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
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
    );
  }
}
