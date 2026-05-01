import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/dashboard_api.dart';
import '../data/dashboard_models.dart';

class DashboardState extends Equatable {
  const DashboardState({
    this.status = LoadStatus.initial,
    this.summary,
    this.error,
  });

  final LoadStatus status;
  final DashboardSummary? summary;
  final String? error;

  DashboardState copyWith({
    LoadStatus? status,
    DashboardSummary? summary,
    String? error,
  }) =>
      DashboardState(
        status: status ?? this.status,
        summary: summary ?? this.summary,
        error: error ?? this.error,
      );

  @override
  List<Object?> get props => [status, summary, error];
}

class DashboardCubit extends Cubit<DashboardState> {
  DashboardCubit(this._api) : super(const DashboardState());

  final DashboardApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading));
    try {
      final summary = await _api.me();
      emit(state.copyWith(status: LoadStatus.success, summary: summary));
    } catch (_) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load dashboard',
      ));
    }
  }
}
