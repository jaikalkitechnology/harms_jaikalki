import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/routing/app_router.dart';
import '../../../core/theme/app_colors.dart';
import '../../team/data/team_api.dart';
import '../data/tasks_api.dart';
import '../widgets/task_widgets.dart';

/// Tasks given to me, by me, and (for managers) to anyone in my team.
class TasksPage extends StatefulWidget {
  const TasksPage({super.key});

  @override
  State<TasksPage> createState() => _TasksPageState();
}

class _TasksPageState extends State<TasksPage> {
  bool? _hasTeam;

  @override
  void initState() {
    super.initState();
    sl<TeamApi>().me().then((t) {
      if (mounted) setState(() => _hasTeam = t.hasTeam);
    }).catchError((_) {
      if (mounted) setState(() => _hasTeam = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_hasTeam == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Tasks')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    final manager = _hasTeam!;
    final tabs = [
      const Tab(text: 'For me'),
      if (manager) const Tab(text: 'Given by me'),
      if (manager) const Tab(text: 'My team'),
    ];
    return DefaultTabController(
      length: tabs.length,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Tasks'),
          bottom: tabs.length > 1 ? TabBar(tabs: tabs) : null,
        ),
        floatingActionButton: manager
            ? FloatingActionButton.extended(
                onPressed: () async {
                  await context.push(AppRoutes.giveTask);
                  if (mounted) setState(() {});
                },
                icon: const Icon(Icons.add_task),
                label: const Text('Give a task'),
              )
            : null,
        body: TabBarView(
          children: [
            const _TaskList(view: 'mine'),
            if (manager) const _TaskList(view: 'given'),
            if (manager) const _TaskList(view: 'team'),
          ],
        ),
      ),
    );
  }
}

class _TaskList extends StatefulWidget {
  const _TaskList({required this.view});
  final String view;

  @override
  State<_TaskList> createState() => _TaskListState();
}

class _TaskListState extends State<_TaskList> with AutomaticKeepAliveClientMixin {
  String _status = 'open';
  late Future<List<WorkTask>> _future = _load();

  Future<List<WorkTask>> _load() =>
      sl<TasksApi>().list(view: widget.view, status: _status);

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);
    return RefreshIndicator(
      onRefresh: _refresh,
      child: FutureBuilder<List<WorkTask>>(
        future: _future,
        builder: (context, snap) {
          final filters = Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Wrap(
              spacing: 8,
              children: [
                for (final f in const [
                  ('open', 'Open'),
                  ('overdue', 'Overdue'),
                  ('done', 'Done'),
                  ('all', 'All'),
                ])
                  ChoiceChip(
                    label: Text(f.$2),
                    selected: _status == f.$1,
                    onSelected: (_) => setState(() {
                      _status = f.$1;
                      _future = _load();
                    }),
                  ),
              ],
            ),
          );
          final children = <Widget>[filters];
          if (snap.hasError) {
            children.add(const Padding(
              padding: EdgeInsets.only(top: 60),
              child: Text('Could not load tasks. Pull down to try again.',
                  textAlign: TextAlign.center, style: TextStyle(color: AppColors.textMuted)),
            ));
          } else if (!snap.hasData) {
            children.add(const Padding(
              padding: EdgeInsets.only(top: 60),
              child: Center(child: CircularProgressIndicator()),
            ));
          } else if (snap.data!.isEmpty) {
            children.add(Padding(
              padding: const EdgeInsets.only(top: 60),
              child: Column(
                children: [
                  const Icon(Icons.task_alt, size: 56, color: AppColors.brandGoldDark),
                  const SizedBox(height: 10),
                  Text(
                    widget.view == 'mine'
                        ? (_status == 'open' ? 'Nothing on your plate right now.' : 'No tasks here.')
                        : 'No tasks here.',
                    style: const TextStyle(color: AppColors.textMuted),
                  ),
                ],
              ),
            ));
          } else {
            for (final t in snap.data!) {
              children.add(TaskCard(
                t: t,
                showAssignee: widget.view != 'mine',
                onTap: () async {
                  await context.push('${AppRoutes.tasks}/${t.id}');
                  _refresh();
                },
              ));
            }
          }
          return ListView(padding: const EdgeInsets.fromLTRB(16, 12, 16, 90), children: children);
        },
      ),
    );
  }
}
