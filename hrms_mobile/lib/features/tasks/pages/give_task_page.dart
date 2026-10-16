import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../../team/data/team_api.dart';
import '../data/tasks_api.dart';

/// Give a task to someone in your team.
class GiveTaskPage extends StatefulWidget {
  const GiveTaskPage({super.key, this.employeeId, this.employeeName});
  final int? employeeId;
  final String? employeeName;

  @override
  State<GiveTaskPage> createState() => _GiveTaskPageState();
}

class _GiveTaskPageState extends State<GiveTaskPage> {
  final _title = TextEditingController();
  final _details = TextEditingController();
  late int? _assignee = widget.employeeId;
  DateTime? _due;
  String _priority = 'medium';
  bool _saving = false;
  late final Future<List<TeamMemberRow>> _people = widget.employeeId != null
      ? Future.value(const <TeamMemberRow>[])
      : sl<TeamApi>().overview(everyone: true).then(
            (o) => [...o.members]..sort((a, b) => a.name.compareTo(b.name)),
          );

  @override
  void dispose() {
    _title.dispose();
    _details.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_assignee == null || _title.text.trim().length < 2) return;
    setState(() => _saving = true);
    try {
      final t = await sl<TasksApi>().create(
        assignedTo: _assignee!,
        title: _title.text.trim(),
        description: _details.text.trim(),
        dueDate: _due == null ? null : DateFormat('yyyy-MM-dd').format(_due!),
        priority: _priority,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Task given to ${t.assigneeName}'),
        backgroundColor: AppColors.success,
      ));
      Navigator.of(context).pop(true);
    } catch (_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Could not create the task.'),
        backgroundColor: AppColors.error,
      ));
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Give a task')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (widget.employeeId != null)
            ListTile(
              contentPadding: EdgeInsets.zero,
              leading: const Icon(Icons.person_outline, color: AppColors.brandGold),
              title: Text(widget.employeeName ?? 'Team member',
                  style: TextStyle(color: context.textPrimary)),
              subtitle: const Text('Gets a notification in the app'),
            )
          else
            FutureBuilder<List<TeamMemberRow>>(
              future: _people,
              builder: (context, snap) {
                if (!snap.hasData) return const LinearProgressIndicator();
                return DropdownButtonFormField<int>(
                  value: _assignee,
                  isExpanded: true,
                  decoration: const InputDecoration(labelText: 'To'),
                  items: [
                    for (final m in snap.data!)
                      DropdownMenuItem(
                        value: m.employeeId,
                        child: Text(
                          '${m.name}${m.designation != null ? ' · ${m.designation}' : ''}',
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                  ],
                  onChanged: (v) => setState(() => _assignee = v),
                );
              },
            ),
          const SizedBox(height: 12),
          TextField(
            controller: _title,
            maxLength: 200,
            decoration: const InputDecoration(labelText: 'Task', hintText: 'What needs doing?'),
            onChanged: (_) => setState(() {}),
          ),
          TextField(
            controller: _details,
            minLines: 2,
            maxLines: 5,
            decoration: const InputDecoration(labelText: 'Details (optional)'),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.event_outlined),
                  label: Text(_due == null ? 'Due date' : DateFormat('d MMM yyyy').format(_due!)),
                  onPressed: () async {
                    final now = DateTime.now();
                    final d = await showDatePicker(
                      context: context,
                      initialDate: _due ?? now.add(const Duration(days: 1)),
                      firstDate: now,
                      lastDate: now.add(const Duration(days: 365)),
                    );
                    if (d != null) setState(() => _due = d);
                  },
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          Text('Priority', style: TextStyle(color: context.textMuted)),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            children: [
              for (final p in taskPriorityLabels.entries)
                ChoiceChip(
                  label: Text(p.value),
                  selected: _priority == p.key,
                  onSelected: (_) => setState(() => _priority = p.key),
                ),
            ],
          ),
          const SizedBox(height: 24),
          FilledButton(
            onPressed: _saving || _assignee == null || _title.text.trim().length < 2 ? null : _save,
            child: Text(_saving ? 'Saving…' : 'Give task'),
          ),
        ],
      ),
    );
  }
}
