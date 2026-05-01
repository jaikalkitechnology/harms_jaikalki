import 'package:equatable/equatable.dart';

class CourseSummary extends Equatable {
  const CourseSummary({
    required this.id,
    required this.code,
    required this.title,
    required this.category,
    required this.difficulty,
    required this.estimatedHours,
    required this.isMandatory,
    required this.points,
    this.description,
    this.thumbnailUrl,
  });

  final int id;
  final String code;
  final String title;
  final String? description;
  final String category;
  final String difficulty;
  final int estimatedHours;
  final bool isMandatory;
  final int points;
  final String? thumbnailUrl;

  factory CourseSummary.fromJson(Map<String, dynamic> j) => CourseSummary(
        id: j['id'] as int,
        code: j['code'] as String,
        title: j['title'] as String,
        description: j['description'] as String?,
        category: j['category'] as String,
        difficulty: j['difficulty'] as String,
        estimatedHours: (j['estimated_hours'] as int?) ?? 1,
        isMandatory: (j['is_mandatory'] as bool?) ?? false,
        points: (j['points'] as int?) ?? 0,
        thumbnailUrl: j['thumbnail_url'] as String?,
      );

  @override
  List<Object?> get props => [id];
}

class Lesson extends Equatable {
  const Lesson({
    required this.id,
    required this.title,
    required this.contentType,
    required this.durationMinutes,
    required this.points,
    this.contentUrl,
    this.articleBody,
  });

  final int id;
  final String title;
  final String contentType;
  final String? contentUrl;
  final String? articleBody;
  final int durationMinutes;
  final int points;

  factory Lesson.fromJson(Map<String, dynamic> j) => Lesson(
        id: j['id'] as int,
        title: j['title'] as String,
        contentType: j['content_type'] as String,
        contentUrl: j['content_url'] as String?,
        articleBody: j['article_body'] as String?,
        durationMinutes: (j['duration_minutes'] as int?) ?? 10,
        points: (j['points'] as int?) ?? 1,
      );

  @override
  List<Object?> get props => [id];
}

class CourseModule extends Equatable {
  const CourseModule({
    required this.id,
    required this.title,
    required this.lessons,
    this.description,
  });

  final int id;
  final String title;
  final String? description;
  final List<Lesson> lessons;

  factory CourseModule.fromJson(Map<String, dynamic> j) => CourseModule(
        id: j['id'] as int,
        title: j['title'] as String,
        description: j['description'] as String?,
        lessons: ((j['lessons'] as List?) ?? const [])
            .map((e) => Lesson.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [id];
}

class CourseDetail extends Equatable {
  const CourseDetail({
    required this.id,
    required this.code,
    required this.title,
    required this.category,
    required this.difficulty,
    required this.estimatedHours,
    required this.isMandatory,
    required this.points,
    required this.modules,
    this.description,
  });

  final int id;
  final String code;
  final String title;
  final String? description;
  final String category;
  final String difficulty;
  final int estimatedHours;
  final bool isMandatory;
  final int points;
  final List<CourseModule> modules;

  factory CourseDetail.fromJson(Map<String, dynamic> j) => CourseDetail(
        id: j['id'] as int,
        code: j['code'] as String,
        title: j['title'] as String,
        description: j['description'] as String?,
        category: j['category'] as String,
        difficulty: j['difficulty'] as String,
        estimatedHours: (j['estimated_hours'] as int?) ?? 1,
        isMandatory: (j['is_mandatory'] as bool?) ?? false,
        points: (j['points'] as int?) ?? 0,
        modules: ((j['modules'] as List?) ?? const [])
            .map((e) => CourseModule.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [id];
}

class Enrollment extends Equatable {
  const Enrollment({
    required this.id,
    required this.employeeId,
    required this.courseId,
    required this.status,
    required this.progressPercentage,
    required this.completedLessonIds,
  });

  final int id;
  final int employeeId;
  final int courseId;
  final String status;
  final int progressPercentage;
  final Set<int> completedLessonIds;

  factory Enrollment.fromJson(Map<String, dynamic> j) {
    final progress = (j['progress'] as List?) ?? const [];
    final completed = <int>{};
    for (final p in progress) {
      final m = p as Map<String, dynamic>;
      if (m['status'] == 'completed') {
        completed.add(m['lesson_id'] as int);
      }
    }
    return Enrollment(
      id: j['id'] as int,
      employeeId: j['employee_id'] as int,
      courseId: j['course_id'] as int,
      status: j['status'] as String,
      progressPercentage: (j['progress_percentage'] as int?) ?? 0,
      completedLessonIds: completed,
    );
  }

  @override
  List<Object?> get props => [id, status, progressPercentage];
}

class LearningStats extends Equatable {
  const LearningStats({
    required this.points,
    required this.coursesCompleted,
    required this.lessonsCompleted,
    required this.streakDays,
    required this.level,
    required this.badges,
  });

  final int points;
  final int coursesCompleted;
  final int lessonsCompleted;
  final int streakDays;
  final String level;
  final List<BadgeOut> badges;

  factory LearningStats.fromJson(Map<String, dynamic> j) => LearningStats(
        points: (j['points'] as int?) ?? 0,
        coursesCompleted: (j['courses_completed'] as int?) ?? 0,
        lessonsCompleted: (j['lessons_completed'] as int?) ?? 0,
        streakDays: (j['streak_days'] as int?) ?? 0,
        level: j['level'] as String? ?? 'bronze',
        badges: ((j['badges'] as List?) ?? const [])
            .map((e) => BadgeOut.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [points, level];
}

class BadgeOut extends Equatable {
  const BadgeOut({
    required this.id,
    required this.code,
    required this.name,
    required this.tier,
    this.description,
    this.icon,
  });

  final int id;
  final String code;
  final String name;
  final String tier;
  final String? description;
  final String? icon;

  factory BadgeOut.fromJson(Map<String, dynamic> j) => BadgeOut(
        id: j['id'] as int,
        code: j['code'] as String,
        name: j['name'] as String,
        tier: j['tier'] as String,
        description: j['description'] as String?,
        icon: j['icon'] as String?,
      );

  @override
  List<Object?> get props => [id];
}
