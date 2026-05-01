import 'package:equatable/equatable.dart';

class AuthUser extends Equatable {
  const AuthUser({
    required this.id,
    required this.email,
    required this.fullName,
    this.phone,
    required this.isActive,
    required this.role,
    required this.roleLevel,
    required this.roles,
    required this.permissions,
  });

  final int id;
  final String email;
  final String fullName;
  final String? phone;
  final bool isActive;
  final String? role;
  final int roleLevel;
  final List<String> roles;
  final List<String> permissions;

  bool hasPermission(String code) =>
      role == 'super_admin' || permissions.contains(code);

  bool hasRole(String code) => roles.contains(code);

  @override
  List<Object?> get props =>
      [id, email, fullName, phone, isActive, role, roleLevel, roles, permissions];
}
