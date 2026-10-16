import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/theme/app_colors.dart';
import '../data/tasks_api.dart';

String fmtTaskDate(String? iso) {
  final d = iso == null ? null : DateTime.tryParse(iso);
  return d == null ? '' : DateFormat('d MMM').format(d);
}

Color taskPriorityColor(String p) => switch (p) {
      'urgent' => AppColors.errorText,
      'high' => AppColors.warning,
      'medium' => AppColors.infoText,
      _ => AppColors.textMuted,
    };

Color taskStatusColor(WorkTask t) {
  if (t.isOverdue) return AppColors.errorText;
  return switch (t.status) {
    'done' => AppColors.successText,
    'in_progress' => AppColors.infoText,
    _ => AppColors.textMuted,
  };
}

class TaskPill extends StatelessWidget {
  const TaskPill(this.label, this.color, {super.key});
  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
        decoration: BoxDecoration(
          color: color.withOpacity(0.15),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(label,
            style: TextStyle(color: color, fontSize: 11.5, fontWeight: FontWeight.w600)),
      );
}

class TaskCard extends StatelessWidget {
  const TaskCard({super.key, required this.t, required this.onTap, this.showAssignee = true});
  final WorkTask t;
  final VoidCallback onTap;
  final bool showAssignee;

  @override
  Widget build(BuildContext context) {
    final who = showAssignee
        ? 'For ${t.assigneeName}${t.assignerName != null ? ' · from ${t.assignerName}' : ''}'
        : (t.assignerName != null ? 'From ${t.assignerName}' : 'My own task');
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: Text(
                      t.title,
                      style: TextStyle(
                        color: context.textPrimary,
                        fontWeight: FontWeight.w600,
                        fontSize: 15,
                        decoration: t.status == 'done' ? TextDecoration.lineThrough : null,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  TaskPill(
                    t.isOverdue ? 'Overdue' : taskStatusLabels[t.status] ?? t.status,
                    taskStatusColor(t),
                  ),
                ],
              ),
              const SizedBox(height: 4),
              Text(who, style: const TextStyle(color: AppColors.textMuted, fontSize: 12.5)),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.event_outlined,
                      size: 15, color: t.isOverdue ? AppColors.errorText : AppColors.textFaint),
                  const SizedBox(width: 4),
                  Text(
                    t.dueDate == null ? 'No due date' : 'Due ${fmtTaskDate(t.dueDate)}',
                    style: TextStyle(
                      fontSize: 12,
                      color: t.isOverdue ? AppColors.errorText : AppColors.textMuted,
                    ),
                  ),
                  const SizedBox(width: 12),
                  TaskPill(taskPriorityLabels[t.priority] ?? t.priority, taskPriorityColor(t.priority)),
                  const Spacer(),
                  if (t.commentCount > 0) ...[
                    const Icon(Icons.chat_bubble_outline, size: 14, color: AppColors.textFaint),
                    const SizedBox(width: 3),
                    Text('${t.commentCount}',
                        style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
