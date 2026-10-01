import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/lms_api.dart';
import '../data/lms_models.dart';

class CourseDetailPage extends StatefulWidget {
  const CourseDetailPage({super.key, required this.courseId});
  final int courseId;

  @override
  State<CourseDetailPage> createState() => _CourseDetailPageState();
}

class _CourseDetailPageState extends State<CourseDetailPage> {
  late Future<({CourseDetail course, Enrollment? enrollment})> _future;
  bool _busy = false;

  @override
  void initState() {
    super.initState();
    _future = _load();
  }

  Future<({CourseDetail course, Enrollment? enrollment})> _load() async {
    final api = sl<LmsApi>();
    final course = await api.getCourse(widget.courseId);
    Enrollment? enr;
    final mine = await api.myCourses();
    for (final e in mine) {
      if (e.courseId == widget.courseId) {
        enr = e;
        break;
      }
    }
    return (course: course, enrollment: enr);
  }

  Future<void> _refresh() async {
    setState(() => _future = _load());
    await _future;
  }

  void _toast(String msg, {bool error = false}) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: error ? AppColors.error : AppColors.success,
      ),
    );
  }

  Future<void> _enroll() async {
    setState(() => _busy = true);
    try {
      await sl<LmsApi>().enroll(widget.courseId);
      _toast('Enrolled');
      await _refresh();
    } catch (_) {
      _toast('Could not enroll', error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _completeLesson(Lesson l) async {
    setState(() => _busy = true);
    try {
      await sl<LmsApi>().completeLesson(
        lessonId: l.id,
        timeSpentSeconds: l.durationMinutes * 60,
      );
      _toast('+${l.points} points!');
      await _refresh();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Could not complete')
          : 'Could not complete';
      _toast(msg, error: true);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _openContent(Lesson l) async {
    if (l.contentUrl != null && l.contentUrl!.trim().isNotEmpty) {
      // canLaunchUrl is unreliable on Android 11+ (package visibility)
      // and was silently swallowing valid links — launch directly and
      // surface any failure instead.
      final uri = Uri.parse(l.contentUrl!.trim());
      try {
        final ok = await launchUrl(
          uri,
          mode: LaunchMode.externalApplication,
        );
        if (!ok && mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Could not open this link')),
          );
        }
      } catch (_) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Cannot open: ${l.contentUrl}')),
          );
        }
      }
    } else if (l.articleBody != null) {
      if (!mounted) return;
      await showModalBottomSheet<void>(
        context: context,
        isScrollControlled: true,
        builder: (_) => DraggableScrollableSheet(
          expand: false,
          initialChildSize: 0.7,
          maxChildSize: 0.95,
          builder: (_, scroll) => SingleChildScrollView(
            controller: scroll,
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l.title,
                    style: Theme.of(context).textTheme.titleLarge),
                const SizedBox(height: 12),
                Text(
                  l.articleBody!,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
              ],
            ),
          ),
        ),
      );
    }
  }

  IconData _iconFor(String contentType) {
    switch (contentType) {
      case 'video':
        return Icons.play_circle_outline;
      case 'pdf':
        return Icons.picture_as_pdf_outlined;
      case 'image':
        return Icons.image_outlined;
      case 'audio':
        return Icons.volume_up_outlined;
      case 'quiz':
        return Icons.quiz_outlined;
      case 'live_session':
        return Icons.video_call_outlined;
      case 'external_link':
        return Icons.open_in_new;
      default:
        return Icons.article_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Course')),
      body: FutureBuilder<({CourseDetail course, Enrollment? enrollment})>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) {
            return const Center(child: CircularProgressIndicator());
          }
          final course = snap.data!.course;
          final enr = snap.data!.enrollment;
          return Stack(
            children: [
              ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(course.title,
                              style: theme.textTheme.titleLarge),
                          const SizedBox(height: 4),
                          Text(
                            '${course.code} · ${course.estimatedHours}h · ${course.difficulty}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: AppColors.textMuted,
                            ),
                          ),
                          if (course.description != null) ...[
                            const SizedBox(height: 8),
                            Text(course.description!,
                                style: theme.textTheme.bodyMedium),
                          ],
                          const SizedBox(height: 12),
                          if (enr == null)
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton.icon(
                                icon: const Icon(Icons.school),
                                label: const Text('Enroll'),
                                onPressed: _busy ? null : _enroll,
                              ),
                            )
                          else
                            Column(
                              children: [
                                LinearProgressIndicator(
                                  value: enr.progressPercentage / 100,
                                  minHeight: 8,
                                  backgroundColor: AppColors.brandBrown50,
                                  valueColor: AlwaysStoppedAnimation(
                                    enr.status == 'completed'
                                        ? AppColors.success
                                        : AppColors.brandGoldDark,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${enr.progressPercentage}% complete · ${enr.status.replaceAll("_", " ")}',
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: AppColors.textMuted,
                                  ),
                                ),
                              ],
                            ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  ...course.modules.map(
                    (m) => Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: Padding(
                        padding: const EdgeInsets.all(12),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(m.title, style: theme.textTheme.titleMedium),
                            if (m.description != null) ...[
                              const SizedBox(height: 4),
                              Text(m.description!,
                                  style: theme.textTheme.bodySmall),
                            ],
                            const SizedBox(height: 8),
                            ...m.lessons.map((l) {
                              final done = enr?.completedLessonIds
                                      .contains(l.id) ??
                                  false;
                              return ListTile(
                                contentPadding: EdgeInsets.zero,
                                leading: Icon(_iconFor(l.contentType),
                                    color: AppColors.brandGoldDark),
                                title: Text(l.title),
                                subtitle: Text(
                                  '${l.durationMinutes} min · ${l.points} pts',
                                  style: theme.textTheme.bodySmall,
                                ),
                                trailing: done
                                    ? Icon(Icons.check_circle,
                                        color: AppColors.success)
                                    : enr == null
                                        ? const Icon(Icons.lock_outline)
                                        : OutlinedButton(
                                            onPressed: _busy
                                                ? null
                                                : () async {
                                                    await _openContent(l);
                                                    await _completeLesson(l);
                                                  },
                                            child: const Text('Start'),
                                          ),
                                onTap: enr == null
                                    ? null
                                    : () => _openContent(l),
                              );
                            }),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
              if (_busy)
                const Positioned.fill(
                  child: ColoredBox(
                    color: Colors.black26,
                    child: Center(child: CircularProgressIndicator()),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
