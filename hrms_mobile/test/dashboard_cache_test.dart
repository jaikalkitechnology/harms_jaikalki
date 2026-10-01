import 'dart:convert';

import 'package:bloc_test/bloc_test.dart';
import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hrms_mobile/core/storage/secure_storage.dart';
import 'package:hrms_mobile/features/dashboard/cubit/dashboard_cubit.dart';
import 'package:hrms_mobile/features/dashboard/data/dashboard_api.dart';
import 'package:hrms_mobile/features/dashboard/data/dashboard_models.dart';
import 'package:hrms_mobile/features/employees/cubit/employees_cubit.dart'
    show LoadStatus;
import 'package:mocktail/mocktail.dart';

class _Api extends Mock implements DashboardApi {}

class _Storage extends Mock implements SecureStorage {}

DashboardSummary _summary(String name) =>
    DashboardSummary.fromJson({'user_full_name': name});

void main() {
  group('DashboardCubit', () {
    late _Api api;
    setUp(() => api = _Api());

    blocTest<DashboardCubit, DashboardState>(
      'shows the saved copy first, then the live data',
      build: () => DashboardCubit(api, userId: 4),
      setUp: () {
        when(() => api.cached(4)).thenAnswer((_) async => _summary('Saved'));
        when(() => api.me(userId: 4)).thenAnswer((_) async => _summary('Live'));
      },
      act: (c) => c.load(),
      expect: () => [
        isA<DashboardState>()
            .having((s) => s.summary?.userFullName, 'name', 'Saved')
            .having((s) => s.fromCache, 'fromCache', true),
        isA<DashboardState>().having((s) => s.refreshing, 'refreshing', true),
        isA<DashboardState>()
            .having((s) => s.summary?.userFullName, 'name', 'Live')
            .having((s) => s.fromCache, 'fromCache', false)
            .having((s) => s.refreshing, 'refreshing', false),
      ],
    );

    blocTest<DashboardCubit, DashboardState>(
      'keeps the saved copy on screen when the refresh fails',
      build: () => DashboardCubit(api, userId: 4),
      setUp: () {
        when(() => api.cached(4)).thenAnswer((_) async => _summary('Saved'));
        when(() => api.me(userId: 4)).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/dashboard/me'),
            type: DioExceptionType.connectionError,
          ),
        );
      },
      act: (c) => c.load(),
      skip: 2,
      expect: () => [
        isA<DashboardState>()
            .having((s) => s.status, 'status', LoadStatus.success)
            .having((s) => s.summary?.userFullName, 'name', 'Saved')
            .having((s) => s.error, 'error', isNotNull),
      ],
    );
  });

  group('DashboardApi.cached', () {
    late _Storage storage;
    late DashboardApi api;

    setUp(() {
      storage = _Storage();
      api = DashboardApi(Dio(), storage);
    });

    String saved(String savedOn) => jsonEncode({
          'saved_on': savedOn,
          'data': {
            'user_full_name': 'Jincy',
            'today_attendance': {'checked_in': true, 'status': 'present'},
          },
        });

    test("drops an earlier day's check-in", () async {
      when(() => storage.readCache('dashboard.4'))
          .thenAnswer((_) async => saved('2000-1-1'));
      final s = await api.cached(4);
      expect(s?.userFullName, 'Jincy');
      expect(s?.todayAttendance.checkedIn, isFalse);
    });

    test("keeps today's check-in", () async {
      final d = DateTime.now();
      when(() => storage.readCache('dashboard.4'))
          .thenAnswer((_) async => saved('${d.year}-${d.month}-${d.day}'));
      final s = await api.cached(4);
      expect(s?.todayAttendance.checkedIn, isTrue);
    });
  });
}
