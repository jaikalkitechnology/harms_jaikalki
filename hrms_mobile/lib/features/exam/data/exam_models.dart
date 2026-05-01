import 'package:equatable/equatable.dart';

class ExamSummary extends Equatable {
  const ExamSummary({
    required this.id,
    required this.code,
    required this.title,
    required this.examType,
    required this.totalQuestions,
    required this.timeLimitMinutes,
    required this.passingPercentage,
    required this.attemptsAllowed,
    this.description,
  });

  final int id;
  final String code;
  final String title;
  final String? description;
  final String examType;
  final int totalQuestions;
  final int timeLimitMinutes;
  final int passingPercentage;
  final int attemptsAllowed;

  factory ExamSummary.fromJson(Map<String, dynamic> j) => ExamSummary(
        id: j['id'] as int,
        code: j['code'] as String,
        title: j['title'] as String,
        description: j['description'] as String?,
        examType: j['exam_type'] as String,
        totalQuestions: (j['total_questions'] as int?) ?? 0,
        timeLimitMinutes: (j['time_limit_minutes'] as int?) ?? 30,
        passingPercentage: (j['passing_percentage'] as int?) ?? 60,
        attemptsAllowed: (j['attempts_allowed'] as int?) ?? 1,
      );

  @override
  List<Object?> get props => [id];
}

class QuestionOption extends Equatable {
  const QuestionOption({
    required this.id,
    required this.optionText,
    required this.sortOrder,
  });

  final int id;
  final String optionText;
  final int sortOrder;

  factory QuestionOption.fromJson(Map<String, dynamic> j) => QuestionOption(
        id: j['id'] as int,
        optionText: j['option_text'] as String,
        sortOrder: (j['sort_order'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [id];
}

class ExamQuestion extends Equatable {
  const ExamQuestion({
    required this.id,
    required this.questionText,
    required this.questionType,
    required this.marks,
    required this.timeSeconds,
    required this.options,
  });

  final int id;
  final String questionText;
  final String questionType;
  final int marks;
  final int timeSeconds;
  final List<QuestionOption> options;

  factory ExamQuestion.fromJson(Map<String, dynamic> j) => ExamQuestion(
        id: j['id'] as int,
        questionText: j['question_text'] as String,
        questionType: j['question_type'] as String,
        marks: (j['marks'] as int?) ?? 1,
        timeSeconds: (j['time_seconds'] as int?) ?? 60,
        options: ((j['options'] as List?) ?? const [])
            .map((e) => QuestionOption.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [id];
}

class ExamSession extends Equatable {
  const ExamSession({
    required this.attemptId,
    required this.startedAt,
    required this.timeLimitMinutes,
    required this.questions,
  });

  final int attemptId;
  final String startedAt;
  final int timeLimitMinutes;
  final List<ExamQuestion> questions;

  factory ExamSession.fromJson(Map<String, dynamic> j) => ExamSession(
        attemptId: j['attempt_id'] as int,
        startedAt: j['started_at'] as String,
        timeLimitMinutes: (j['time_limit_minutes'] as int?) ?? 30,
        questions: ((j['questions'] as List?) ?? const [])
            .map((e) => ExamQuestion.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  @override
  List<Object?> get props => [attemptId];
}

class AttemptResult extends Equatable {
  const AttemptResult({
    required this.id,
    required this.examId,
    required this.totalScore,
    required this.maxScore,
    required this.percentage,
    required this.status,
    required this.passed,
  });

  final int id;
  final int examId;
  final int totalScore;
  final int maxScore;
  final double percentage;
  final String status;
  final bool passed;

  factory AttemptResult.fromJson(Map<String, dynamic> j) => AttemptResult(
        id: j['id'] as int,
        examId: j['exam_id'] as int,
        totalScore: (j['total_score'] as int?) ?? 0,
        maxScore: (j['max_score'] as int?) ?? 0,
        percentage:
            double.tryParse(j['percentage'].toString()) ?? 0,
        status: j['status'] as String,
        passed: (j['passed'] as bool?) ?? false,
      );

  @override
  List<Object?> get props => [id, status];
}

class CertificateOut extends Equatable {
  const CertificateOut({
    required this.id,
    required this.certificateNumber,
    required this.title,
    required this.issuedDate,
    this.expiryDate,
    this.scorePercentage,
  });

  final int id;
  final String certificateNumber;
  final String title;
  final String issuedDate;
  final String? expiryDate;
  final double? scorePercentage;

  factory CertificateOut.fromJson(Map<String, dynamic> j) => CertificateOut(
        id: j['id'] as int,
        certificateNumber: j['certificate_number'] as String,
        title: j['title'] as String,
        issuedDate: j['issued_date'] as String,
        expiryDate: j['expiry_date'] as String?,
        scorePercentage: j['score_percentage'] != null
            ? double.tryParse(j['score_percentage'].toString())
            : null,
      );

  @override
  List<Object?> get props => [id];
}
