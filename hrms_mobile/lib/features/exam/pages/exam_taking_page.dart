import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../../../core/di/injection.dart';
import '../../../core/theme/app_colors.dart';
import '../data/exam_api.dart';
import '../data/exam_models.dart';

class ExamTakingPage extends StatefulWidget {
  const ExamTakingPage({super.key, required this.examId});
  final int examId;

  @override
  State<ExamTakingPage> createState() => _ExamTakingPageState();
}

class _ExamTakingPageState extends State<ExamTakingPage>
    with WidgetsBindingObserver {
  ExamSession? _session;
  int _index = 0;
  int _secondsLeft = 0;
  Timer? _timer;
  final Map<int, List<int>> _selections = {};
  final Map<int, int> _timePerQuestion = {};
  DateTime _questionStartedAt = DateTime.now();
  bool _busy = false;
  bool _submitted = false;
  AttemptResult? _result;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _start();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _timer?.cancel();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    // Treat app backgrounding as a tab-switch flag
    if (state == AppLifecycleState.paused && _session != null && !_submitted) {
      sl<ExamApi>()
          .flag(attemptId: _session!.attemptId, flagType: 'tab_switch')
          .catchError((_) {});
    }
  }

  Future<void> _start() async {
    setState(() => _busy = true);
    try {
      final s = await sl<ExamApi>().start(widget.examId);
      setState(() {
        _session = s;
        _secondsLeft = s.timeLimitMinutes * 60;
        _questionStartedAt = DateTime.now();
      });
      _timer = Timer.periodic(const Duration(seconds: 1), (_) {
        if (!mounted) return;
        setState(() => _secondsLeft -= 1);
        if (_secondsLeft <= 0) {
          _timer?.cancel();
          _submit(autoSubmit: true);
        }
      });
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Could not start')
          : 'Could not start';
      _showError(msg);
      if (mounted) Navigator.of(context).pop();
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  void _showError(String msg) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(msg),
        backgroundColor: AppColors.error,
      ),
    );
  }

  void _trackTime() {
    final q = _session!.questions[_index];
    final delta = DateTime.now().difference(_questionStartedAt).inSeconds;
    _timePerQuestion[q.id] = (_timePerQuestion[q.id] ?? 0) + delta;
    _questionStartedAt = DateTime.now();
  }

  void _toggleOption(int questionId, int optionId, bool multiple) {
    final list = List<int>.from(_selections[questionId] ?? const []);
    if (multiple) {
      if (list.contains(optionId)) {
        list.remove(optionId);
      } else {
        list.add(optionId);
      }
    } else {
      list
        ..clear()
        ..add(optionId);
    }
    setState(() => _selections[questionId] = list);
  }

  Future<void> _submit({bool autoSubmit = false}) async {
    if (_session == null || _submitted) return;
    setState(() => _busy = true);
    _trackTime();
    final answers = _session!.questions
        .where((q) => (_selections[q.id] ?? const []).isNotEmpty)
        .map(
          (q) => {
            'question_id': q.id,
            'selected_option_ids': _selections[q.id],
            'time_taken_seconds': _timePerQuestion[q.id] ?? 0,
          },
        )
        .toList();
    try {
      final result = await sl<ExamApi>().submit(
        attemptId: _session!.attemptId,
        answers: answers,
      );
      setState(() {
        _result = result;
        _submitted = true;
      });
      _timer?.cancel();
    } on DioException catch (e) {
      final msg = e.response?.data is Map
          ? (e.response!.data['detail']?.toString() ?? 'Could not submit')
          : 'Could not submit';
      _showError(msg);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  String _formatTime(int s) {
    final m = (s ~/ 60).toString().padLeft(2, '0');
    final sec = (s % 60).toString().padLeft(2, '0');
    return '$m:$sec';
  }

  @override
  Widget build(BuildContext context) {
    if (_session == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Loading exam')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }
    if (_submitted && _result != null) {
      return _ResultView(result: _result!);
    }
    final q = _session!.questions[_index];
    final isMultiple = q.questionType == 'multiple_choice';
    final selected = _selections[q.id] ?? const [];
    final lowTime = _secondsLeft < 60;
    return PopScope(
      canPop: false,
      onPopInvokedWithResult: (didPop, _) async {
        if (didPop) return;
        final go = await showDialog<bool>(
          context: context,
          builder: (_) => AlertDialog(
            title: const Text('Quit exam?'),
            content: const Text(
              'You will lose your progress. Submit instead?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context, false),
                child: const Text('Cancel'),
              ),
              TextButton(
                onPressed: () => Navigator.pop(context, true),
                child: const Text('Quit'),
              ),
            ],
          ),
        );
        if (go == true && mounted) Navigator.of(context).pop();
      },
      child: Scaffold(
        appBar: AppBar(
          title: Text('Q ${_index + 1}/${_session!.questions.length}'),
          actions: [
            Center(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Row(
                  children: [
                    Icon(Icons.timer,
                        size: 16,
                        color: lowTime
                            ? AppColors.error
                            : AppColors.brandGoldDark),
                    const SizedBox(width: 4),
                    Text(
                      _formatTime(_secondsLeft),
                      style: TextStyle(
                        color: lowTime
                            ? AppColors.error
                            : AppColors.brandBrownDarker,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
        body: Stack(
          children: [
            Column(
              children: [
                LinearProgressIndicator(
                  value: (_index + 1) / _session!.questions.length,
                  backgroundColor: AppColors.brandBrown50,
                  valueColor: const AlwaysStoppedAnimation(
                      AppColors.brandGoldDark),
                ),
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      Text(
                        q.questionText,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        '${q.marks} mark${q.marks == 1 ? "" : "s"}'
                        '${isMultiple ? " · multiple correct" : ""}',
                        style: Theme.of(context)
                            .textTheme
                            .bodySmall
                            ?.copyWith(color: AppColors.brandBrownLight),
                      ),
                      const SizedBox(height: 16),
                      ...q.options.map(
                        (o) => _OptionTile(
                          option: o,
                          selected: selected.contains(o.id),
                          multiple: isMultiple,
                          onTap: () =>
                              _toggleOption(q.id, o.id, isMultiple),
                        ),
                      ),
                    ],
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Row(
                    children: [
                      OutlinedButton(
                        onPressed: _index == 0 || _busy
                            ? null
                            : () {
                                _trackTime();
                                setState(() => _index -= 1);
                              },
                        child: const Text('Previous'),
                      ),
                      const Spacer(),
                      if (_index < _session!.questions.length - 1)
                        ElevatedButton(
                          onPressed: _busy
                              ? null
                              : () {
                                  _trackTime();
                                  setState(() => _index += 1);
                                },
                          child: const Text('Next'),
                        )
                      else
                        ElevatedButton.icon(
                          icon: const Icon(Icons.send),
                          label: const Text('Submit'),
                          onPressed: _busy ? null : () => _submit(),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: AppColors.success,
                          ),
                        ),
                    ],
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
        ),
      ),
    );
  }
}

class _OptionTile extends StatelessWidget {
  const _OptionTile({
    required this.option,
    required this.selected,
    required this.multiple,
    required this.onTap,
  });
  final QuestionOption option;
  final bool selected;
  final bool multiple;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: selected ? AppColors.brandGoldPale : null,
      child: ListTile(
        leading: Icon(
          multiple
              ? (selected
                  ? Icons.check_box
                  : Icons.check_box_outline_blank)
              : (selected
                  ? Icons.radio_button_checked
                  : Icons.radio_button_unchecked),
          color: selected
              ? AppColors.brandGoldDark
              : AppColors.brandBrownLight,
        ),
        title: Text(option.optionText),
        onTap: onTap,
      ),
    );
  }
}

class _ResultView extends StatelessWidget {
  const _ResultView({required this.result});
  final AttemptResult result;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final color =
        result.passed ? AppColors.success : AppColors.error;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Result'),
        leading: const SizedBox.shrink(),
        automaticallyImplyLeading: false,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                result.passed
                    ? Icons.emoji_events
                    : Icons.sentiment_dissatisfied,
                size: 96,
                color: color,
              ),
              const SizedBox(height: 16),
              Text(
                result.passed ? 'Passed!' : 'Did not pass',
                style: theme.textTheme.headlineMedium?.copyWith(color: color),
              ),
              const SizedBox(height: 8),
              Text(
                '${result.percentage.toStringAsFixed(1)}%',
                style: theme.textTheme.headlineLarge?.copyWith(
                  color: AppColors.brandGoldDark,
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Score: ${result.totalScore} / ${result.maxScore}',
                style: theme.textTheme.titleMedium,
              ),
              const SizedBox(height: 32),
              ElevatedButton.icon(
                icon: const Icon(Icons.check),
                label: const Text('Done'),
                onPressed: () => context.go('/exams'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
