import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/approval_api.dart';
import '../data/approval_models.dart';

class ApprovalsInboxState extends Equatable {
  const ApprovalsInboxState({
    this.status = LoadStatus.initial,
    this.items = const [],
    this.counts = const [],
    this.filter,
    this.error,
  });

  final LoadStatus status;
  final List<ApprovalItem> items;
  final List<ApprovalCount> counts;
  final String? filter;
  final String? error;

  ApprovalsInboxState copyWith({
    LoadStatus? status,
    List<ApprovalItem>? items,
    List<ApprovalCount>? counts,
    String? filter,
    String? error,
    bool clearFilter = false,
    bool clearError = false,
  }) =>
      ApprovalsInboxState(
        status: status ?? this.status,
        items: items ?? this.items,
        counts: counts ?? this.counts,
        filter: clearFilter ? null : (filter ?? this.filter),
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, items, counts, filter, error];
}

class ApprovalsInboxCubit extends Cubit<ApprovalsInboxState> {
  ApprovalsInboxCubit(this._api) : super(const ApprovalsInboxState());

  final ApprovalApi _api;

  Future<void> load({String? filter, bool clearFilter = false}) async {
    emit(state.copyWith(
      status: LoadStatus.loading,
      filter: filter,
      clearFilter: clearFilter,
      clearError: true,
    ));
    try {
      final results = await Future.wait([
        _api.inbox(requestType: clearFilter ? null : (filter ?? state.filter)),
        _api.counts(),
      ]);
      emit(state.copyWith(
        status: LoadStatus.success,
        items: results[0] as List<ApprovalItem>,
        counts: results[1] as List<ApprovalCount>,
      ));
    } catch (_) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load approvals',
      ));
    }
  }

  Future<void> approve(int id) async {
    try {
      await _api.approve(id, comments: 'Approved');
      await load();
    } catch (e) {
      emit(state.copyWith(error: _detail(e)));
    }
  }

  Future<void> reject(int id) async {
    try {
      await _api.reject(id, comments: 'Rejected');
      await load();
    } catch (e) {
      emit(state.copyWith(error: _detail(e)));
    }
  }

  String _detail(Object e) {
    final s = e.toString();
    final m = RegExp(r'detail":\s*"([^"]+)"').firstMatch(s);
    return m?.group(1) ?? 'Could not act on approval';
  }
}
