import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../features/approvals/pages/approvals_inbox_page.dart';
import '../../features/attendance/pages/attendance_home_page.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/auth/presentation/pages/login_page.dart';
import '../../features/dashboard/dashboard_page.dart';
import '../../features/employees/pages/employee_detail_page.dart';
import '../../features/employees/pages/employees_list_page.dart';
import '../../features/intern_expenses/pages/intern_expenses_page.dart';
import '../../features/leaves/pages/leaves_home_page.dart';
import '../../features/leaves/pages/manager_inbox_page.dart';
import '../../features/splash/splash_page.dart';
import '../di/injection.dart';

class AppRoutes {
  AppRoutes._();
  static const splash = '/';
  static const login = '/login';
  static const dashboard = '/dashboard';
  static const directorDashboard = '/director/dashboard';
  static const hrDashboard = '/hr/dashboard';
  static const managerDashboard = '/manager/dashboard';
  static const employeeDashboard = '/employee/dashboard';
  static const employees = '/employees';
  static const internExpenses = '/intern/expenses';
  static const attendance = '/attendance';
  static const leaves = '/leaves';
  static const managerInbox = '/manager/inbox';
  static const approvalsInbox = '/approvals';

  static String dashboardFor(String? role) {
    switch (role) {
      case 'director':
      case 'super_admin':
        return directorDashboard;
      case 'hr':
        return hrDashboard;
      case 'manager':
        return managerDashboard;
      case 'intern':
        return internExpenses;
      case 'employee':
      case 'trainer':
      case 'field':
        return employeeDashboard;
      default:
        return dashboard;
    }
  }
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

      if (auth.status == AuthStatus.initial ||
          auth.status == AuthStatus.loading) {
        return onSplash ? null : AppRoutes.splash;
      }

      if (!auth.isAuthenticated) {
        return loggingIn ? null : AppRoutes.login;
      }

      if (loggingIn || onSplash) {
        return AppRoutes.dashboardFor(auth.user?.role);
      }
      return null;
    },
    routes: [
      GoRoute(
        path: AppRoutes.splash,
        builder: (_, __) => const SplashPage(),
      ),
      GoRoute(
        path: AppRoutes.login,
        builder: (_, __) => BlocProvider<AuthBloc>.value(
          value: sl<AuthBloc>(),
          child: const LoginPage(),
        ),
      ),
      GoRoute(
        path: AppRoutes.dashboard,
        builder: (_, __) => const DashboardPage(),
      ),
      GoRoute(
        path: AppRoutes.directorDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'Director'),
      ),
      GoRoute(
        path: AppRoutes.hrDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'HR'),
      ),
      GoRoute(
        path: AppRoutes.managerDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'Manager'),
      ),
      GoRoute(
        path: AppRoutes.employeeDashboard,
        builder: (_, __) => const DashboardPage(roleLabel: 'Employee'),
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
