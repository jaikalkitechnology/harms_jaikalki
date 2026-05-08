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
import '../../features/exam/pages/exam_list_page.dart';
import '../../features/exam/pages/exam_taking_page.dart';
import '../../features/exam/pages/my_certificates_page.dart';
import '../../features/polish/data/polish_models.dart';
import '../../features/visitors/pages/visitor_pass_page.dart';
import '../../features/visitors/pages/visitor_register_page.dart';
import '../../features/visitors/pages/visitor_scan_page.dart';
import '../../features/visitors/pages/visitors_home_page.dart';
import '../../features/launch/pages/resignation_page.dart';
import '../../features/field/pages/field_home_page.dart';
import '../../features/field/pages/field_live_map_page.dart';
import '../../features/field/pages/field_visit_page.dart';
import '../../features/intern_expenses/pages/intern_expenses_page.dart';
import '../../features/justice/pages/justice_gate_page.dart';
import '../../features/justice/pages/justice_resources_page.dart';
import '../../features/justice/pages/justice_submit_page.dart';
import '../../features/leaves/pages/leaves_home_page.dart';
import '../../features/leaves/pages/manager_inbox_page.dart';
import '../../features/lms/pages/badges_page.dart';
import '../../features/lms/pages/course_detail_page.dart';
import '../../features/lms/pages/lms_home_page.dart';
import '../../features/onboarding/onboarding_page.dart';
import '../../features/payroll/pages/payroll_home_page.dart';
import '../../features/performance/pages/feedback_inbox_page.dart';
import '../../features/launch/pages/forgot_password_page.dart';
import '../../features/launch/pages/mfa_setup_page.dart';
import '../../features/launch/pages/notifications_page.dart';
import '../../features/performance/pages/goals_page.dart';
import '../../features/polish/pages/book_room_page.dart';
import '../../features/polish/pages/jobs_page.dart';
import '../../features/polish/pages/my_assets_page.dart';
import '../../features/reports/pages/director_dashboard_page.dart';
import '../../features/sales/pages/lead_detail_page.dart';
import '../../features/sales/pages/my_leads_page.dart';
import '../../features/sales/pages/new_lead_page.dart';
import '../../features/sales/pages/sales_pipeline_page.dart';
import '../../features/sales/pages/sales_targets_page.dart';
import '../../features/trainer/pages/sessions_page.dart';
import '../../features/trainer/pages/trainer_marketplace_page.dart';
import '../../features/verification/pages/verification_form_page.dart';
import '../../features/verification/pages/verification_queue_page.dart';
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
  static const payroll = '/payroll';
  static const justice = '/justice';
  static const justiceSubmit = '/justice/submit';
  static const justiceResources = '/justice/resources';
  static const fieldHome = '/field';
  static const fieldLiveMap = '/field/live-map';
  static const salesPipeline = '/sales/pipeline';
  static const salesTargets = '/sales/targets';
  static const myLeads = '/sales/leads';
  static const newLead = '/sales/leads/new';
  static const verificationQueue = '/verification';
  static const lmsHome = '/lms';
  static const lmsBadges = '/lms/badges';
  static const exams = '/exams';
  static const myCertificates = '/exams/me/certificates';
  static const visitors = '/visitors';
  static const visitorRegister = '/visitors/new';
  static const visitorScan = '/visitors/scan';
  static const visitorPass = '/visitors/pass';
  static const resignation = '/resignation';
  static const trainers = '/trainers';
  static const trainerSessions = '/trainers/sessions';
  static const myGoals = '/performance/goals';
  static const feedbackInbox = '/performance/feedback';
  static const directorDashboard = '/reports/dashboard';
  static const myAssets = '/polish/assets';
  static const bookRoom = '/polish/rooms';
  static const browseJobs = '/polish/jobs';
  static const notifications = '/notifications';
  static const mfaSetup = '/mfa/setup';
  static const forgotPassword = '/forgot-password';

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
      final onForgotPassword = loc == AppRoutes.forgotPassword;

      if (auth.status == AuthStatus.initial ||
          auth.status == AuthStatus.loading) {
        return onSplash ? null : AppRoutes.splash;
      }

      if (!auth.isAuthenticated) {
        // First-launch onboarding gate before login. Forgot-password is
        // also reachable without auth.
        if (!onOnboarding && !loggingIn && !onForgotPassword) {
          final onboarded = sl<SettingsCubit>().state.onboardingCompleted;
          if (!onboarded) return AppRoutes.onboarding;
          return AppRoutes.login;
        }
        return null;
      }

      if (loggingIn || onSplash || onOnboarding || onForgotPassword) {
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
      GoRoute(
        path: AppRoutes.payroll,
        builder: (_, __) => const PayrollHomePage(),
      ),
      GoRoute(
        path: AppRoutes.justice,
        builder: (_, __) => const JusticeGatePage(),
      ),
      GoRoute(
        path: AppRoutes.justiceSubmit,
        builder: (_, __) => const JusticeSubmitPage(),
      ),
      GoRoute(
        path: AppRoutes.justiceResources,
        builder: (_, __) => const JusticeResourcesPage(),
      ),
      GoRoute(
        path: AppRoutes.fieldHome,
        builder: (_, __) => const FieldHomePage(),
      ),
      GoRoute(
        path: AppRoutes.fieldLiveMap,
        builder: (_, __) => const FieldLiveMapPage(),
      ),
      GoRoute(
        path: '/field/visit/:jobId',
        builder: (_, state) => FieldVisitPage(
          jobId: int.parse(state.pathParameters['jobId']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.salesPipeline,
        builder: (_, __) => const SalesPipelinePage(),
      ),
      GoRoute(
        path: AppRoutes.salesTargets,
        builder: (_, __) => const SalesTargetsPage(),
      ),
      GoRoute(
        path: AppRoutes.myLeads,
        builder: (_, __) => const MyLeadsPage(),
      ),
      GoRoute(
        path: AppRoutes.newLead,
        builder: (_, __) => const NewLeadPage(),
      ),
      GoRoute(
        path: '/sales/leads/:id',
        builder: (_, state) => LeadDetailPage(
          leadId: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.verificationQueue,
        builder: (_, __) => const VerificationQueuePage(),
      ),
      GoRoute(
        path: '/verification/:id',
        builder: (_, state) => VerificationFormPage(
          verificationId: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.lmsHome,
        builder: (_, __) => const LmsHomePage(),
      ),
      GoRoute(
        path: AppRoutes.lmsBadges,
        builder: (_, __) => const BadgesPage(),
      ),
      GoRoute(
        path: '/lms/course/:id',
        builder: (_, state) => CourseDetailPage(
          courseId: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.exams,
        builder: (_, __) => const ExamListPage(),
      ),
      GoRoute(
        path: '/exams/:id/take',
        builder: (_, state) => ExamTakingPage(
          examId: int.parse(state.pathParameters['id']!),
        ),
      ),
      GoRoute(
        path: AppRoutes.myCertificates,
        builder: (_, __) => const MyCertificatesPage(),
      ),
      GoRoute(
        path: AppRoutes.visitors,
        builder: (_, __) => const VisitorsHomePage(),
      ),
      GoRoute(
        path: AppRoutes.resignation,
        builder: (_, __) => const ResignationPage(),
      ),
      GoRoute(
        path: AppRoutes.visitorRegister,
        builder: (_, __) => const VisitorRegisterPage(),
      ),
      GoRoute(
        path: AppRoutes.visitorScan,
        builder: (_, __) => const VisitorScanPage(),
      ),
      GoRoute(
        path: '${AppRoutes.visitorPass}/:id',
        builder: (_, state) {
          final extra = state.extra;
          if (extra is Visitor) {
            return VisitorPassPage(visitor: extra);
          }
          return const Scaffold(
            body: Center(child: Text('Visitor pass not found')),
          );
        },
      ),
      GoRoute(
        path: AppRoutes.trainers,
        builder: (_, __) => const TrainerMarketplacePage(),
      ),
      GoRoute(
        path: AppRoutes.trainerSessions,
        builder: (_, __) => const TrainerSessionsPage(),
      ),
      GoRoute(
        path: AppRoutes.myGoals,
        builder: (_, __) => const MyGoalsPage(),
      ),
      GoRoute(
        path: AppRoutes.feedbackInbox,
        builder: (_, __) => const FeedbackInboxPage(),
      ),
      GoRoute(
        path: AppRoutes.directorDashboard,
        builder: (_, __) => const DirectorDashboardPage(),
      ),
      GoRoute(
        path: AppRoutes.myAssets,
        builder: (_, __) => const MyAssetsPage(),
      ),
      GoRoute(
        path: AppRoutes.bookRoom,
        builder: (_, __) => const BookRoomPage(),
      ),
      GoRoute(
        path: AppRoutes.browseJobs,
        builder: (_, __) => const JobsPage(),
      ),
      GoRoute(
        path: AppRoutes.notifications,
        builder: (_, __) => const NotificationsPage(),
      ),
      GoRoute(
        path: AppRoutes.mfaSetup,
        builder: (_, __) => const MfaSetupPage(),
      ),
      GoRoute(
        path: AppRoutes.forgotPassword,
        builder: (_, __) => const ForgotPasswordPage(),
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
