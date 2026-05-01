import '../../domain/entities/auth_user.dart';

class UserModel {
  const UserModel({
    required this.id,
    required this.email,
    required this.fullName,
    this.phone,
    required this.isActive,
  });

  final int id;
  final String email;
  final String fullName;
  final String? phone;
  final bool isActive;

  factory UserModel.fromJson(Map<String, dynamic> json) => UserModel(
        id: json['id'] as int,
        email: json['email'] as String,
        fullName: (json['full_name'] as String?) ?? '',
        phone: json['phone'] as String?,
        isActive: (json['is_active'] as bool?) ?? true,
      );
}

class MeResponseModel {
  const MeResponseModel({
    required this.user,
    required this.role,
    required this.roleLevel,
    required this.roles,
    required this.permissions,
  });

  final UserModel user;
  final String? role;
  final int roleLevel;
  final List<String> roles;
  final List<String> permissions;

  factory MeResponseModel.fromJson(Map<String, dynamic> json) => MeResponseModel(
        user: UserModel.fromJson(json['user'] as Map<String, dynamic>),
        role: json['role'] as String?,
        roleLevel: (json['role_level'] as int?) ?? 0,
        roles: List<String>.from(json['roles'] as List? ?? const []),
        permissions:
            List<String>.from(json['permissions'] as List? ?? const []),
      );

  AuthUser toEntity() => AuthUser(
        id: user.id,
        email: user.email,
        fullName: user.fullName,
        phone: user.phone,
        isActive: user.isActive,
        role: role,
        roleLevel: roleLevel,
        roles: roles,
        permissions: permissions,
      );
}
