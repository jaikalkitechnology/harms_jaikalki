import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../data/employee_api.dart';
import '../data/employee_models.dart';

enum LoadStatus { initial, loading, success, failure }

class EmployeesState extends Equatable {
  const EmployeesState({
    this.status = LoadStatus.initial,
    this.items = const [],
    this.search = '',
    this.error,
  });

  final LoadStatus status;
  final List<EmployeeListItem> items;
  final String search;
  final String? error;

  EmployeesState copyWith({
    LoadStatus? status,
    List<EmployeeListItem>? items,
    String? search,
    String? error,
    bool clearError = false,
  }) =>
      EmployeesState(
        status: status ?? this.status,
        items: items ?? this.items,
        search: search ?? this.search,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, items, search, error];
}

class EmployeesCubit extends Cubit<EmployeesState> {
  EmployeesCubit(this._api) : super(const EmployeesState());

  final EmployeeApi _api;

  Future<void> load({String? search}) async {
    emit(state.copyWith(
      status: LoadStatus.loading,
      search: search ?? state.search,
      clearError: true,
    ));
    try {
      final items = await _api.list(search: search ?? state.search);
      emit(state.copyWith(status: LoadStatus.success, items: items));
    } catch (e) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load employees',
      ));
    }
  }
}
