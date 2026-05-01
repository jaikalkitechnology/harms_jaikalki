import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/leave_api.dart';
import '../data/leave_models.dart';

class LeavesState extends Equatable {
  const LeavesState({
    this.status = LoadStatus.initial,
    this.types = const [],
    this.balances = const [],
    this.requests = const [],
    this.busy = false,
    this.error,
  });

  final LoadStatus status;
  final List<LeaveType> types;
  final List<LeaveBalance> balances;
  final List<LeaveRequest> requests;
  final bool busy;
  final String? error;

  LeavesState copyWith({
    LoadStatus? status,
    List<LeaveType>? types,
    List<LeaveBalance>? balances,
    List<LeaveRequest>? requests,
    bool? busy,
    String? error,
    bool clearError = false,
  }) =>
      LeavesState(
        status: status ?? this.status,
        types: types ?? this.types,
        balances: balances ?? this.balances,
        requests: requests ?? this.requests,
        busy: busy ?? this.busy,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, types, balances, requests, busy, error];
}

class LeavesCubit extends Cubit<LeavesState> {
  LeavesCubit(this._api) : super(const LeavesState());

  final LeaveApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading, clearError: true));
    try {
      final results = await Future.wait([
        _api.types(),
        _api.balance(),
        _api.myRequests(),
      ]);
      emit(state.copyWith(
        status: LoadStatus.success,
        types: results[0] as List<LeaveType>,
        balances: results[1] as List<LeaveBalance>,
        requests: results[2] as List<LeaveRequest>,
      ));
    } catch (e) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load leaves',
      ));
    }
  }

  Future<bool> apply({
    required int leaveTypeId,
    required String fromDate,
    required String toDate,
    String? reason,
    bool halfDay = false,
  }) async {
    emit(state.copyWith(busy: true, clearError: true));
    try {
      await _api.apply(
        leaveTypeId: leaveTypeId,
        fromDate: fromDate,
        toDate: toDate,
        reason: reason,
        halfDay: halfDay,
      );
      emit(state.copyWith(busy: false));
      await load();
      return true;
    } catch (e) {
      emit(state.copyWith(busy: false, error: _detail(e)));
      return false;
    }
  }

  Future<void> cancel(int id) async {
    await _api.cancel(id);
    await load();
  }

  String _detail(Object e) {
    final s = e.toString();
    final m = RegExp(r'detail":\s*"([^"]+)"').firstMatch(s);
    return m?.group(1) ?? 'Could not submit leave';
  }
}

class PendingApprovalsState extends Equatable {
  const PendingApprovalsState({
    this.status = LoadStatus.initial,
    this.items = const [],
    this.error,
  });
  final LoadStatus status;
  final List<LeaveRequest> items;
  final String? error;

  PendingApprovalsState copyWith({
    LoadStatus? status,
    List<LeaveRequest>? items,
    String? error,
  }) =>
      PendingApprovalsState(
        status: status ?? this.status,
        items: items ?? this.items,
        error: error ?? this.error,
      );

  @override
  List<Object?> get props => [status, items, error];
}

class PendingApprovalsCubit extends Cubit<PendingApprovalsState> {
  PendingApprovalsCubit(this._api) : super(const PendingApprovalsState());

  final LeaveApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading));
    try {
      final items = await _api.pending();
      emit(state.copyWith(status: LoadStatus.success, items: items));
    } catch (_) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load pending requests',
      ));
    }
  }

  Future<void> approve(int id) async {
    await _api.approve(id, comment: 'Approved');
    await load();
  }

  Future<void> reject(int id) async {
    await _api.reject(id, comment: 'Rejected');
    await load();
  }
}
