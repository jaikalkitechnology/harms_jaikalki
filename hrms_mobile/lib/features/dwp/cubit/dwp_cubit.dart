import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/dwp_api.dart';
import '../data/dwp_models.dart';

class DwpHomeState extends Equatable {
  const DwpHomeState({
    this.status = LoadStatus.initial,
    this.today = const [],
    this.history = const [],
    this.streakDays = 0,
    this.error,
  });

  final LoadStatus status;
  final List<DwpSubmission> today;
  final List<DwpSubmission> history;
  final int streakDays;
  final String? error;

  bool get hasMorning => today.any((s) => s.type == 'morning');
  bool get hasEod => today.any((s) => s.type == 'eod');

  DwpHomeState copyWith({
    LoadStatus? status,
    List<DwpSubmission>? today,
    List<DwpSubmission>? history,
    int? streakDays,
    String? error,
  }) =>
      DwpHomeState(
        status: status ?? this.status,
        today: today ?? this.today,
        history: history ?? this.history,
        streakDays: streakDays ?? this.streakDays,
        error: error ?? this.error,
      );

  @override
  List<Object?> get props => [status, today, history, streakDays, error];
}

class DwpHomeCubit extends Cubit<DwpHomeState> {
  DwpHomeCubit(this._api) : super(const DwpHomeState());
  final DwpApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading));
    try {
      final today = await _api.myToday();
      final history = await _api.myHistory(limit: 30);
      // Best-effort streak via morning template (cheap, gets streak from server).
      int streak = 0;
      try {
        final t = await _api.morningTemplate();
        streak = t.streakDays;
      } catch (_) {}
      emit(state.copyWith(
        status: LoadStatus.success,
        today: today,
        history: history,
        streakDays: streak,
      ));
    } catch (_) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load DWP',
      ));
    }
  }
}

class DwpFormState extends Equatable {
  const DwpFormState({
    this.status = LoadStatus.initial,
    this.template,
    this.prefill = const {},
    this.linkedMorningId,
    this.submitting = false,
    this.error,
  });

  final LoadStatus status;
  final DwpTemplate? template;
  final Map<String, dynamic> prefill;
  final int? linkedMorningId;
  final bool submitting;
  final String? error;

  DwpFormState copyWith({
    LoadStatus? status,
    DwpTemplate? template,
    Map<String, dynamic>? prefill,
    int? linkedMorningId,
    bool? submitting,
    String? error,
    bool clearError = false,
  }) =>
      DwpFormState(
        status: status ?? this.status,
        template: template ?? this.template,
        prefill: prefill ?? this.prefill,
        linkedMorningId: linkedMorningId ?? this.linkedMorningId,
        submitting: submitting ?? this.submitting,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props =>
      [status, template, prefill, linkedMorningId, submitting, error];
}

class DwpFormCubit extends Cubit<DwpFormState> {
  DwpFormCubit(this._api, this.type) : super(const DwpFormState());

  final DwpApi _api;
  final String type;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading, clearError: true));
    try {
      final t = type == 'morning'
          ? await _api.morningTemplate()
          : await _api.eodTemplate();
      emit(state.copyWith(
        status: LoadStatus.success,
        template: t.template,
        prefill: t.prefill,
        linkedMorningId: t.linkedMorningId,
      ));
    } catch (_) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load template',
      ));
    }
  }

  Future<bool> submit(Map<String, dynamic> values) async {
    final tpl = state.template;
    if (tpl == null) return false;
    emit(state.copyWith(submitting: true, clearError: true));
    try {
      final hours = num.tryParse('${values['hours_planned'] ?? values['hours_actual'] ?? ''}');
      final mood = int.tryParse('${values['mood_rating'] ?? ''}');
      if (type == 'morning') {
        await _api.submitMorning(
          templateId: tpl.id,
          fields: values,
          totalHours: hours,
          moodRating: mood,
        );
      } else {
        await _api.submitEod(
          templateId: tpl.id,
          fields: values,
          totalHours: hours,
          moodRating: mood,
        );
      }
      emit(state.copyWith(submitting: false));
      return true;
    } catch (e) {
      emit(state.copyWith(
        submitting: false,
        error: _detail(e),
      ));
      return false;
    }
  }

  String _detail(Object e) {
    final s = e.toString();
    final m = RegExp(r'detail":\s*"([^"]+)"').firstMatch(s);
    return m?.group(1) ?? 'Could not submit';
  }
}
