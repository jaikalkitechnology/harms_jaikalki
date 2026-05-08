import 'package:flutter/material.dart';

import '../../l10n/app_l10n.dart';
import '../attendance/pages/attendance_home_page.dart';
import '../dashboard/dashboard_page.dart';
import '../more/more_menu_page.dart';
import '../profile/profile_page.dart';

/// Persistent bottom-nav shell hosting the 4 primary tabs (Home /
/// Attendance / More / Profile). Approvals moved into the More menu.
class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final l = AppL10n.of(context);
    final pages = const [
      DashboardPage(),
      AttendanceHomePage(),
      MoreMenuPage(),
      ProfilePage(),
    ];

    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: const Icon(Icons.home),
            label: l.home,
          ),
          NavigationDestination(
            icon: const Icon(Icons.fingerprint_outlined),
            selectedIcon: const Icon(Icons.fingerprint),
            label: l.attendance,
          ),
          NavigationDestination(
            icon: const Icon(Icons.grid_view_outlined),
            selectedIcon: const Icon(Icons.grid_view),
            label: l.more,
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline),
            selectedIcon: const Icon(Icons.person),
            label: l.profile,
          ),
        ],
      ),
    );
  }
}
