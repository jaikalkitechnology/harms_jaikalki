import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/tasks_api.dart';
import '../widgets/task_widgets.dart';

/// One task: details, progress buttons, and the comment thread.
class TaskDetailPage extends StatefulWidget {
  const TaskDetailPage({super.key, required this.taskId});
  final int taskId;

  @override
  State<TaskDetailPage> createState() => _TaskDetailPageState();
}

class _TaskDetailPageState extends State<TaskDetailPage> {
  late Future<WorkTask> _task = sl<TasksApi>().get(widget.taskId);
  late Future<List<TaskComment>> _comments = sl<TasksApi>().comments(widget.taskId);
  final _comment = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  void _reload() => setState(() {
        _task = sl<TasksApi>().get(widget.taskId);
        _comments = sl<TasksApi>().comments(widget.taskId);
      });

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(msg),
      backgroundColor: error ? AppColors.error : AppColors.success,
    ));
  }

  Future<void> _update(Map<String, dynamic> changes, String done) async {
    setState(() => _busy = true);
    try {
      await sl<TasksApi>().update(widget.taskId, changes);
      _toast(done);
      _reload();
    } catch (_) {
      _toast('Could not update the task.', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _markDone() async {
    final note = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Mark as done'),
        content: TextField(
          controller: note,
          maxLines: 3,
          decoration: const InputDecoration(hintText: 'What was done? (optional)'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Done')),
        ],
      ),
    );
    if (ok == true) {
      await _update(
        {'status': 'done', if (note.text.trim().isNotEmpty) 'completion_note': note.text.trim()},
        'Marked as done',
      );
    }
  }

  Future<void> _changeDue(WorkTask t) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: DateTime.tryParse(t.dueDate ?? '') ?? now,
      firstDate: now.subtract(const Duration(days: 365)),
      lastDate: now.add(const Duration(days: 365)),
    );
    if (picked != null) {
      await _update({'due_date': DateFormat('yyyy-MM-dd').format(picked)}, 'Due date changed');
    }
  }

  Future<void> _send() async {
    final body = _comment.text.trim();
    if (body.isEmpty) return;
    try {
      await sl<TasksApi>().addComment(widget.taskId, body);
      _comment.clear();
      setState(() => _comments = sl<TasksApi>().comments(widget.taskId));
    } catch (_) {
      _toast('Could not send the comment.', error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Task'),
        actions: [
          FutureBuilder<WorkTask>(
            future: _task,
            builder: (context, snap) {
              final t = snap.data;
              if (t == null || !t.canManage) return const SizedBox.shrink();
              return PopupMenuButton<String>(
                onSelected: (v) async {
                  if (v == 'due') await _changeDue(t);
                  if (v == 'cancel') await _update({'status': 'cancelled'}, 'Task cancelled');
                  if (v.startsWith('p:')) await _update({'priority': v.substring(2)}, 'Priority changed');
                  if (v == 'delete') {
                    await sl<TasksApi>().delete(t.id);
                    if (context.mounted) Navigator.of(context).pop();
                  }
                },
                itemBuilder: (_) => [
                  const PopupMenuItem(value: 'due', child: Text('Change due date')),
                  for (final p in taskPriorityLabels.entries)
                    PopupMenuItem(value: 'p:${p.key}', child: Text('Priority: ${p.value}')),
                  if (t.status != 'cancelled')
                    const PopupMenuItem(value: 'cancel', child: Text('Cancel task')),
                  const PopupMenuItem(value: 'delete', child: Text('Delete')),
                ],
              );
            },
          ),
        ],
      ),
      body: FutureBuilder<WorkTask>(
        future: _task,
        builder: (context, snap) {
          if (snap.hasError) {
            return const Center(
              child: Text('Could not load this task.', style: TextStyle(color: AppColors.textMuted)),
            );
          }
          if (!snap.hasData) return const Center(child: CircularProgressIndicator());
          final t = snap.data!;
          final canProgress = t.isMine || t.canManage;
          return Column(
            children: [
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    Text(t.title,
                        style: TextStyle(
                          color: context.textPrimary,
                          fontSize: 20,
                          fontWeight: FontWeight.w700,
                        )),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 6,
                      children: [
                        TaskPill(t.isOverdue ? 'Overdue' : taskStatusLabels[t.status] ?? t.status,
                            taskStatusColor(t)),
                        TaskPill(taskPriorityLabels[t.priority] ?? t.priority, taskPriorityColor(t.priority)),
                      ],
                    ),
                    const SizedBox(height: 14),
                    _Info('For', t.assigneeName),
                    if (t.assignerName != null) _Info('From', t.assignerName!),
                    _Info('Due', t.dueDate == null ? 'No due date' : fmtTaskDate(t.dueDate),
                        color: t.isOverdue ? AppColors.errorText : null),
                    if (t.completedAt != null)
                      _Info('Done', '${fmtTaskDate(t.completedAt)}'
                          '${t.completionNote != null ? ' — ${t.completionNote}' : ''}',
                          color: AppColors.successText),
                    if (t.escalationLevel > 1)
                      Padding(
                        padding: const EdgeInsets.only(top: 6),
                        child: Text(
                          'Running late — escalated ${t.escalationLevel - 1} level'
                          '${t.escalationLevel > 2 ? 's' : ''} up.',
                          style: const TextStyle(color: AppColors.warning, fontSize: 12.5),
                        ),
                      ),
                    if ((t.description ?? '').isNotEmpty) ...[
                      const SizedBox(height: 12),
                      Text(t.description!,
                          style: TextStyle(color: context.textPrimary, height: 1.4)),
                    ],
                    if (canProgress && t.status != 'cancelled') ...[
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          if (t.status != 'in_progress' && t.status != 'done')
                            Expanded(
                              child: OutlinedButton(
                                onPressed: _busy
                                    ? null
                                    : () => _update({'status': 'in_progress'}, 'Marked in progress'),
                                child: const Text('Start'),
                              ),
                            ),
                          if (t.status != 'done') ...[
                            const SizedBox(width: 10),
                            Expanded(
                              child: FilledButton.icon(
                                onPressed: _busy ? null : _markDone,
                                icon: const Icon(Icons.check),
                                label: const Text('Mark done'),
                              ),
                            ),
                          ] else
                            Expanded(
                              child: OutlinedButton(
                                onPressed: _busy
                                    ? null
                                    : () => _update({'status': 'open'}, 'Reopened'),
                                child: const Text('Reopen'),
                              ),
                            ),
                        ],
                      ),
                    ],
                    const SizedBox(height: 20),
                    Text('COMMENTS',
                        style: Theme.of(context)
                            .textTheme
                            .labelSmall
                            ?.copyWith(color: AppColors.brandGoldDark, letterSpacing: 1)),
                    const SizedBox(height: 8),
                    FutureBuilder<List<TaskComment>>(
                      future: _comments,
                      builder: (context, cs) {
                        final list = cs.data ?? const <TaskComment>[];
                        if (!cs.hasData) return const LinearProgressIndicator();
                        if (list.isEmpty) {
                          return const Text('No comments yet.',
                              style: TextStyle(color: AppColors.textMuted));
                        }
                        return Column(
                          children: [
                            for (final c in list)
                              Container(
                                width: double.infinity,
                                margin: const EdgeInsets.only(bottom: 8),
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: AppColors.brandGold.withOpacity(0.08),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text('${c.author} · ${fmtTaskDate(c.createdAt)}',
                                        style: const TextStyle(color: AppColors.textMuted, fontSize: 11.5)),
                                    const SizedBox(height: 2),
                                    Text(c.body, style: TextStyle(color: context.textPrimary)),
                                  ],
                                ),
                              ),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
              SafeArea(
                top: false,
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(12, 6, 8, 8),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _comment,
                          minLines: 1,
                          maxLines: 3,
                          decoration: const InputDecoration(hintText: 'Write a comment…'),
                        ),
                      ),
                      IconButton(
                        onPressed: _send,
                        icon: const Icon(Icons.send, color: AppColors.brandGold),
                        tooltip: 'Send',
                      ),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _Info extends StatelessWidget {
  const _Info(this.label, this.value, {this.color});
  final String label;
  final String value;
  final Color? color;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 3),
        child: Row(
          children: [
            SizedBox(
              width: 56,
              child: Text(label, style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
            ),
            Expanded(
              child: Text(value,
                  style: TextStyle(color: color ?? context.textPrimary, fontWeight: FontWeight.w500)),
            ),
          ],
        ),
      );
}
