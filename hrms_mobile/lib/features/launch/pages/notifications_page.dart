import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../data/launch_api.dart';

class NotificationsPage extends StatefulWidget {
  const NotificationsPage({super.key});

  @override
  State<NotificationsPage> createState() => _NotificationsPageState();
}

class _NotificationsPageState extends State<NotificationsPage> {
  late Future<List<NotificationItem>> _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = sl<LaunchApi>().myNotifications();
  }

  Future<void> _refresh() async {
    setState(() => _future = sl<LaunchApi>().myNotifications());
    await _future;
  }

  Future<void> _markAll() async {
    setState(() => _busy = true);
    try {
      final n = await sl<LaunchApi>().markAllRead();
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('$n marked as read'),
            backgroundColor: AppColors.success,
          ),
        );
      }
      await _refresh();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _markOne(NotificationItem n) async {
    if (n.isRead) return;
    await sl<LaunchApi>().markRead(n.id);
    await _refresh();
  }

  /// Where tapping a notification of this type takes you, if anywhere.
  static String? _destination(NotificationItem n) => switch (n.type) {
        'letter_issued' => AppRoutes.documents,
        'policy_published' => '${AppRoutes.documents}?tab=policies',
        'certificate_issued' => AppRoutes.myCertificates,
        'task_assigned' || 'task_done' || 'task_comment' || 'task_overdue' ||
        'task_escalated' =>
          n.data?['task_id'] != null ? '${AppRoutes.tasks}/${n.data!['task_id']}' : AppRoutes.tasks,
        'team_digest' || 'team_weekly' => AppRoutes.myTeam,
        'target_behind' => AppRoutes.salesTargets,
        'plan_reminder' => AppRoutes.dwp,
        _ => null,
      };

  void _open(NotificationItem n) {
    final dest = _destination(n);
    if (dest == null) {
      _markOne(n);
      return;
    }
    // Mark read in the background; the list refreshes on the way back.
    if (!n.isRead) {
      sl<LaunchApi>().markRead(n.id).then((_) {
        if (mounted) _refresh();
      }).catchError((_) {});
    }
    context.push(dest);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          IconButton(
            icon: const Icon(Icons.done_all),
            tooltip: 'Mark all read',
            onPressed: _busy ? null : _markAll,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refresh,
        child: FutureBuilder<List<NotificationItem>>(
          future: _future,
          builder: (context, snap) {
            if (!snap.hasData) {
              return const Center(child: CircularProgressIndicator());
            }
            final items = snap.data!;
            if (items.isEmpty) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.notifications_none,
                          size: 64, color: AppColors.brandGoldDark),
                      const SizedBox(height: 12),
                      Text(
                        "You're all caught up.",
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: AppColors.textMuted,
                        ),
                      ),
                    ],
                  ),
                ),
              );
            }
            return ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: items.length,
              itemBuilder: (context, i) {
                final n = items[i];
                return Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  // Unread: a light gold tint that keeps the text readable
                  // in both themes.
                  color: n.isRead ? null : AppColors.brandGold.withOpacity(0.14),
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: AppColors.brandGoldPale,
                      child: Icon(
                        n.isRead ? Icons.notifications : Icons.notifications_active,
                        color: AppColors.brandGoldDark,
                      ),
                    ),
                    title: Text(
                      n.title,
                      style: TextStyle(
                        color: context.textPrimary,
                        fontWeight: n.isRead ? FontWeight.normal : FontWeight.bold,
                      ),
                    ),
                    subtitle: Text(
                      n.body ?? n.type,
                      style: theme.textTheme.bodySmall
                          ?.copyWith(color: AppColors.textMuted),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    trailing: !n.isRead
                        ? IconButton(
                            icon: const Icon(Icons.check_circle_outline),
                            onPressed: () => _markOne(n),
                          )
                        : null,
                    onTap: () => _open(n),
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
