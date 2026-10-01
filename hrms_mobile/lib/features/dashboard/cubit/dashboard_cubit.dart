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
    this.fromCache = false,
    this.refreshing = false,
  });

  final LoadStatus status;
  final DashboardSummary? summary;
  final String? error;

  /// [summary] is the saved copy from the last visit, not live data.
  final bool fromCache;

  /// A fetch is running while the current [summary] stays on screen.
  final bool refreshing;

  DashboardState copyWith({
    LoadStatus? status,
    DashboardSummary? summary,
    String? error,
    bool clearError = false,
    bool? fromCache,
    bool? refreshing,
  }) =>
      DashboardState(
        status: status ?? this.status,
        summary: summary ?? this.summary,
        error: clearError ? null : (error ?? this.error),
        fromCache: fromCache ?? this.fromCache,
        refreshing: refreshing ?? this.refreshing,
      );

  @override
  List<Object?> get props => [status, summary, error, fromCache, refreshing];
}

class DashboardCubit extends Cubit<DashboardState> {
  DashboardCubit(this._api, {this.userId}) : super(const DashboardState());

  final DashboardApi _api;

  /// Signed-in user; enables the saved copy shown before live data.
  final int? userId;

  Future<void> load() async {
    final uid = userId;
    if (state.summary == null && uid != null) {
      final cached = await _api.cached(uid);
      if (cached != null && state.summary == null && !isClosed) {
        emit(state.copyWith(
          status: LoadStatus.success,
          summary: cached,
          fromCache: true,
        ));
      }
    }
    if (isClosed) return;
    emit(state.copyWith(
      status: state.summary == null ? LoadStatus.loading : null,
      refreshing: true,
      clearError: true,
    ));
    try {
      final summary = await _api.me(userId: uid);
      if (isClosed) return;
      emit(state.copyWith(
        status: LoadStatus.success,
        summary: summary,
        fromCache: false,
        refreshing: false,
      ));
    } catch (_) {
      if (isClosed) return;
      emit(state.copyWith(
        // Keep showing what we have; only fail when there is nothing.
        status: state.summary == null ? LoadStatus.failure : null,
        refreshing: false,
        error: 'Could not load dashboard',
      ));
    }
  }
}
