import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/approvals/pages/approvals_inbox_page.dart';
import '../../features/attendance/pages/attendance_home_page.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/dwp/pages/dwp_form_page.dart';
import '../../features/dwp/pages/dwp_home_page.dart';
import '../../features/employees/pages/employee_detail_page.dart';
import '../../features/employees/pages/employees_list_page.dart';
import '../../features/intern_expenses/pages/intern_expenses_page.dart';
import '../../features/leaves/pages/leaves_home_page.dart';
import '../../features/leaves/pages/manager_inbox_page.dart';
import '../../features/onboarding/onboarding_page.dart';
import '../../features/settings/cubit/settings_cubit.dart';
import '../../features/settings/pages/settings_page.dart';
import '../../features/shell/home_shell.dart';
import '../../features/splash/splash_page.dart';
import '../di/injection.dart';

class AppRoutes {
  AppRoutes._();
  static const splash = '/';
  static const onboarding = '/onboarding';
  static const login = '/login';
  static const home = '/home';
  // Legacy aliases — all roles land on /home (the bottom-nav shell).
  static const dashboard = home;
  static const directorDashboard = home;
  static const hrDashboard = home;
  static const managerDashboard = home;
  static const employeeDashboard = home;

  static const employees = '/employees';
  static const internExpenses = '/intern/expenses';
  static const attendance = '/attendance';
  static const leaves = '/leaves';
  static const managerInbox = '/manager/inbox';
  static const approvalsInbox = '/approvals';
  static const settings = '/settings';
  static const dwp = '/dwp';
  static const dwpMorning = '/dwp/morning';
  static const dwpEod = '/dwp/eod';

  static String dashboardFor(String? role) => home;
}

GoRouter buildRouter(AuthBloc authBloc) {
  return GoRouter(
    initialLocation: AppRoutes.splash,
    refreshListenable: _BlocStream(authBloc.stream),
    redirect: (context, state) {
      final auth = authBloc.state;
      final loc = state.matchedLocation;
      final loggingIn = loc == AppRoutes.login;
      final onSplash = loc == AppRoutes.splash;
      final onOnboarding = loc == AppRoutes.onboarding;

      if (auth.status == AuthStatus.initial ||
          auth.status == AuthStatus.loading) {
        return onSplash ? null : AppRoutes.splash;
      }

      if (!auth.isAuthenticated) {
        // First-launch onboarding gate before login.
        if (!onOnboarding && !loggingIn) {
          final onboarded = sl<SettingsCubit>().state.onboardingCompleted;
          if (!onboarded) return AppRoutes.onboarding;
          return AppRoutes.login;
        }
        return null;
      }

      if (loggingIn || onSplash || onOnboarding) {
        return AppRoutes.home;
      }
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (_, __) => const SplashPage(),
      ),
      GoRoute(
        path: AppRoutes.onboarding,
        builder: (_, __) => BlocProvider.value(
          value: sl<SettingsCubit>(),
          child: const OnboardingPage(),
        ),
      ),
      GoRoute(
        path: AppRoutes.login,
        // The root AuthBloc is provided at MaterialApp level — don't wrap
        // again or the login form would dispatch to a stale factory bloc.
        builder: (_, __) => const LoginPage(),
      ),
      GoRoute(
        path: AppRoutes.home,
        builder: (_, __) => const HomeShell(),
      ),
      GoRoute(
        path: AppRoutes.settings,
        builder: (_, __) => BlocProvider.value(
          value: sl<SettingsCubit>(),
          child: const SettingsPage(),
        ),
      ),
      GoRoute(
        path: AppRoutes.employees,
        builder: (_, __) => const EmployeesListPage(),
      ),
      GoRoute(
        path: '/employees/:id',
        builder: (_, state) => EmployeeDetailPage(
          employeeId: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.internExpenses,
        builder: (_, __) => const InternExpensesPage(),
      ),
      GoRoute(
        path: AppRoutes.attendance,
        builder: (_, __) => const AttendanceHomePage(),
      ),
      GoRoute(
        path: AppRoutes.leaves,
        builder: (_, __) => const LeavesHomePage(),
      ),
      GoRoute(
        path: AppRoutes.managerInbox,
        builder: (_, __) => const ManagerInboxPage(),
      ),
      GoRoute(
        path: AppRoutes.approvalsInbox,
        builder: (_, __) => const ApprovalsInboxPage(),
      ),
      GoRoute(
        path: AppRoutes.dwp,
        builder: (_, __) => const DwpHomePage(),
      ),
      GoRoute(
        path: AppRoutes.dwpMorning,
        builder: (_, __) => const DwpFormPage(type: 'morning'),
      ),
      GoRoute(
        path: AppRoutes.dwpEod,
        builder: (_, __) => const DwpFormPage(type: 'eod'),
      ),
    ],
  );
}

class _BlocStream extends ChangeNotifier {
  _BlocStream(Stream<dynamic> stream) {
    _sub = stream.listen((_) => notifyListeners());
  }
  late final StreamSubscription<dynamic> _sub;

  @override
  void dispose() {
    _sub.cancel();
    super.dispose();
  }
}
