import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/lms_api.dart';
import '../data/lms_models.dart';

class LmsHomePage extends StatefulWidget {
  const LmsHomePage({super.key});

  @override
  State<LmsHomePage> createState() => _LmsHomePageState();
}

class _LmsHomePageState extends State<LmsHomePage> {
  late Future<({List<CourseSummary> courses, LearningStats stats})> _future;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({List<CourseSummary> courses, LearningStats stats})> _load() async {
    final api = sl<LmsApi>();
    final courses = await api.courses();
    final stats = await api.myStats();
    return (courses: courses, stats: stats);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  Color _categoryColor(String c) {
    switch (c) {
      case 'compliance':
        return AppColors.error;
      case 'onboarding':
        return AppColors.info;
      case 'leadership':
        return AppColors.warning;
      case 'soft_skills':
        return AppColors.success;
      default:
        return AppColors.brandGoldDark;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Learning'),
        actions: [
          IconButton(
            icon: const Icon(Icons.emoji_events_outlined),
            tooltip: 'My badges',
            onPressed: () => context.push('/lms/badges'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child:
            FutureBuilder<({List<CourseSummary> courses, LearningStats stats})>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final courses = snap.data!.courses;
            final stats = snap.data!.stats;
            return ListView(
              padding: const EdgeInsets.all(16),
              children: [
                _StatsCard(stats: stats),
                const SizedBox(height: 16),
                Text('★ COURSES (${courses.length})',
                    style: theme.textTheme.labelSmall?.copyWith(
                      color: AppColors.brandGoldDark,
                    )),
                const SizedBox(height: 8),
                ...courses.map(
                  (c) => Card(
                    margin: const EdgeInsets.only(bottom: 12),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(12),
                      onTap: () => context.push('/lms/course/${c.id}'),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    c.title,
                                    style: theme.textTheme.titleMedium,
                                  ),
                                ),
                                if (c.isMandatory)
                                  Container(
                                    padding: const EdgeInsets.symmetric(
                                        horizontal: 8, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: AppColors.error.withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: const Text(
                                      'MANDATORY',
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: AppColors.error,
                                      ),
                                    ),
                                  ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            Row(
                              children: [
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 8, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: _categoryColor(c.category)
                                        .withOpacity(0.15),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    c.category.replaceAll('_', ' '),
                                    style: TextStyle(
                                      fontSize: 10,
                                      color: _categoryColor(c.category),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Text('${c.estimatedHours}h · ${c.difficulty}',
                                    style: theme.textTheme.bodySmall),
                              ],
                            ),
                            if (c.description != null) ...[
                              const SizedBox(height: 8),
                              Text(
                                c.description!,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  color: AppColors.brandBrownLight,
                                ),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ],
                            const SizedBox(height: 8),
                            Row(
                              children: [
                                Icon(Icons.workspace_premium,
                                    size: 16,
                                    color: AppColors.brandGoldDark),
                                const SizedBox(width: 4),
                                Text('${c.points} pts',
                                    style: theme.textTheme.bodySmall),
                                const Spacer(),
                                const Icon(Icons.chevron_right, size: 16),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
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

class _StatsCard extends StatelessWidget {
  const _StatsCard({required this.stats});
  final LearningStats stats;

  Color _levelColor(String level) {
    switch (level) {
      case 'platinum':
        return AppColors.info;
      case 'gold':
        return AppColors.brandGoldDark;
      case 'silver':
        return AppColors.brandBrownLight;
      default:
        return AppColors.warning;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      color: AppColors.brandGoldPale,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.local_fire_department,
                    color: AppColors.warning, size: 28),
                const SizedBox(width: 8),
                Text(
                  '${stats.streakDays}-day streak',
                  style: theme.textTheme.titleMedium,
                ),
                const Spacer(),
                Container(
                  padding: const EdgeInsets.symmetric(
                      horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: _levelColor(stats.level),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    stats.level.toUpperCase(),
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 11,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                _Stat(label: 'Points', value: stats.points.toString()),
                _Stat(
                  label: 'Courses',
                  value: stats.coursesCompleted.toString(),
                ),
                _Stat(
                  label: 'Lessons',
                  value: stats.lessonsCompleted.toString(),
                ),
                _Stat(label: 'Badges', value: stats.badges.length.toString()),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat({required this.label, required this.value});
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
                color: AppColors.brandGoldDark,
              ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.brandBrownLight,
              ),
        ),
      ],
    );
  }
}
