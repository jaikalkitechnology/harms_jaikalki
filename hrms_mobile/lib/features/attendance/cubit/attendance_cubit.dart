import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:geolocator/geolocator.dart';
import 'package:image_picker/image_picker.dart';

import '../../employees/cubit/employees_cubit.dart' show LoadStatus;
import '../data/attendance_api.dart';
import '../data/attendance_models.dart';

class AttendanceState extends Equatable {
  const AttendanceState({
    this.status = LoadStatus.initial,
    this.today,
    this.history = const [],
    this.busy = false,
    this.error,
  });

  final LoadStatus status;
  final AttendanceRecord? today;
  final List<AttendanceRecord> history;
  final bool busy;
  final String? error;

  AttendanceState copyWith({
    LoadStatus? status,
    AttendanceRecord? today,
    List<AttendanceRecord>? history,
    bool? busy,
    String? error,
    bool clearError = false,
    bool clearToday = false,
  }) =>
      AttendanceState(
        status: status ?? this.status,
        today: clearToday ? null : (today ?? this.today),
        history: history ?? this.history,
        busy: busy ?? this.busy,
        error: clearError ? null : (error ?? this.error),
      );

  @override
  List<Object?> get props => [status, today, history, busy, error];
}

class AttendanceCubit extends Cubit<AttendanceState> {
  AttendanceCubit(this._api) : super(const AttendanceState());

  final AttendanceApi _api;

  Future<void> load() async {
    emit(state.copyWith(status: LoadStatus.loading, clearError: true));
    try {
      final records = await _api.myRecords();
      final todayStr = DateTime.now().toIso8601String().substring(0, 10);
      final today = records.where((r) => r.date == todayStr).cast<AttendanceRecord?>().firstWhere(
            (_) => true,
            orElse: () => null,
          );
      emit(state.copyWith(
        status: LoadStatus.success,
        history: records,
        today: today,
        clearToday: today == null,
      ));
    } catch (e) {
      emit(state.copyWith(
        status: LoadStatus.failure,
        error: 'Could not load attendance',
      ));
    }
  }

  Future<({double lat, double lng})?> _resolvePosition() async {
    final perm = await Geolocator.checkPermission();
    if (perm == LocationPermission.denied) {
      final asked = await Geolocator.requestPermission();
      if (asked == LocationPermission.denied ||
          asked == LocationPermission.deniedForever) {
        return null;
      }
    }
    final pos = await Geolocator.getCurrentPosition();
    return (lat: pos.latitude, lng: pos.longitude);
  }

  Future<XFile?> _pickSelfie() async {
    final picker = ImagePicker();
    final picked = await picker.pickImage(
      source: ImageSource.camera,
      preferredCameraDevice: CameraDevice.front,
      imageQuality: 80,
      maxWidth: 1080,
    );
    return picked;
  }

  Future<bool> checkIn({required String workMode}) async {
    emit(state.copyWith(busy: true, clearError: true));
    try {
      final pos = await _resolvePosition();
      if (pos == null) {
        emit(state.copyWith(busy: false, error: 'Location permission denied'));
        return false;
      }
      XFile? selfie;
      if (workMode == 'wfh') {
        selfie = await _pickSelfie();
        if (selfie == null) {
          emit(state.copyWith(
            busy: false,
            error: 'Selfie required for WFH check-in',
          ));
          return false;
        }
      }
      final record = await _api.checkInWithSelfie(
        lat: pos.lat,
        lng: pos.lng,
        workMode: workMode,
        selfie: selfie,
      );
      emit(state.copyWith(busy: false, today: record));
      await load();
      return true;
    } catch (e) {
      final detail = _extractDetail(e);
      emit(state.copyWith(busy: false, error: detail));
      return false;
    }
  }

  Future<bool> checkOut() async {
    emit(state.copyWith(busy: true, clearError: true));
    try {
      final pos = await _resolvePosition();
      final record = await _api.checkOut(lat: pos?.lat, lng: pos?.lng);
      emit(state.copyWith(busy: false, today: record));
      await load();
      return true;
    } catch (e) {
      emit(state.copyWith(busy: false, error: _extractDetail(e)));
      return false;
    }
  }

  String _extractDetail(Object e) {
    final s = e.toString();
    final m = RegExp(r'detail":\s*"([^"]+)"').firstMatch(s);
    if (m != null) return m.group(1)!;
    return 'Something went wrong';
  }
}
