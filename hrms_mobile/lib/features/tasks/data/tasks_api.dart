import 'package:dio/dio.dart';

class WorkTask {
  const WorkTask(this.j);
  final Map<String, dynamic> j;

  int get id => j['id'] as int;
  String get title => j['title'] as String? ?? '';
  String? get description => j['description'] as String?;
  int get assignedTo => j['assigned_to'] as int;
  String get assigneeName => j['assignee_name'] as String? ?? '';
  String? get assignerName => j['assigner_name'] as String?;
  String? get dueDate => j['due_date'] as String?;
  String get priority => j['priority'] as String? ?? 'medium';
  String get status => j['status'] as String? ?? 'open';
  bool get isOverdue => j['is_overdue'] as bool? ?? false;
  String? get completedAt => j['completed_at'] as String?;
  String? get completionNote => j['completion_note'] as String?;
  int get escalationLevel => j['escalation_level'] as int? ?? 0;
  int get commentCount => j['comment_count'] as int? ?? 0;
  String? get createdAt => j['created_at'] as String?;
  bool get canManage => j['can_manage'] as bool? ?? false;
  bool get isMine => j['is_mine'] as bool? ?? false;
  bool get isOpen => status == 'open' || status == 'in_progress';
}

class TaskComment {
  const TaskComment(this.j);
  final Map<String, dynamic> j;
  int get id => j['id'] as int;
  String get author => j['author_name'] as String? ?? '';
  String get body => j['body'] as String? ?? '';
  String? get createdAt => j['created_at'] as String?;
}

const taskPriorityLabels = {
  'low': 'Low',
  'medium': 'Medium',
  'high': 'High',
  'urgent': 'Urgent',
};

const taskStatusLabels = {
  'open': 'To do',
  'in_progress': 'In progress',
  'done': 'Done',
  'cancelled': 'Cancelled',
};

class TasksApi {
  TasksApi(this._dio);
  final Dio _dio;
  static const _v1 = '/api/v1';

  /// view: mine (given to me) · given (by me) · team.
  Future<List<WorkTask>> list({
    required String view,
    String status = 'open',
    int? employeeId,
  }) async {
    final res = await _dio.get<List<dynamic>>(
      '$_v1/tasks',
      queryParameters: {
        'view': view,
        'status': status,
        if (employeeId != null) 'employee_id': employeeId,
      },
    );
    return (res.data ?? const [])
        .map((e) => WorkTask(e as Map<String, dynamic>))
        .toList();
  }

  Future<WorkTask> get(int id) async {
    final res = await _dio.get<Map<String, dynamic>>('$_v1/tasks/$id');
    return WorkTask(res.data!);
  }

  Future<WorkTask> create({
    required int assignedTo,
    required String title,
    String? description,
    String? dueDate,
    String priority = 'medium',
  }) async {
    final res = await _dio.post<Map<String, dynamic>>('$_v1/tasks', data: {
      'assigned_to': assignedTo,
      'title': title,
      if (description != null && description.isNotEmpty) 'description': description,
      if (dueDate != null) 'due_date': dueDate,
      'priority': priority,
    });
    return WorkTask(res.data!);
  }

  Future<WorkTask> update(int id, Map<String, dynamic> changes) async {
    final res = await _dio.patch<Map<String, dynamic>>('$_v1/tasks/$id', data: changes);
    return WorkTask(res.data!);
  }

  Future<void> delete(int id) => _dio.delete<void>('$_v1/tasks/$id');

  Future<List<TaskComment>> comments(int id) async {
    final res = await _dio.get<List<dynamic>>('$_v1/tasks/$id/comments');
    return (res.data ?? const [])
        .map((e) => TaskComment(e as Map<String, dynamic>))
        .toList();
  }

  Future<TaskComment> addComment(int id, String body) async {
    final res = await _dio.post<Map<String, dynamic>>(
      '$_v1/tasks/$id/comments',
      data: {'body': body},
    );
    return TaskComment(res.data!);
  }
}
