import 'package:equatable/equatable.dart';

class EmployeeCategory extends Equatable {
  const EmployeeCategory({
    required this.id,
    required this.code,
    required this.name,
    required this.onlyTravelExpense,
    required this.requiresProbation,
  });

  final int id;
  final String code;
  final String name;
  final bool onlyTravelExpense;
  final bool requiresProbation;

  factory EmployeeCategory.fromJson(Map<String, dynamic> json) =>
      EmployeeCategory(
        id: json['id'] as int,
        code: json['code'] as String,
        name: json['name'] as String,
        onlyTravelExpense: (json['only_travel_expense'] as bool?) ?? false,
        requiresProbation: (json['requires_probation'] as bool?) ?? false,
      );

  @override
  List<Object?> get props => [id, code];
}

class Department extends Equatable {
  const Department({required this.id, required this.code, required this.name});
  final int id;
  final String code;
  final String name;

  factory Department.fromJson(Map<String, dynamic> json) => Department(
        id: json['id'] as int,
        code: json['code'] as String,
        name: json['name'] as String,
      );

  @override
  List<Object?> get props => [id, code];
}

class Designation extends Equatable {
  const Designation({
    required this.id,
    required this.code,
    required this.name,
    required this.level,
  });
  final int id;
  final String code;
  final String name;
  final int level;

  factory Designation.fromJson(Map<String, dynamic> json) => Designation(
        id: json['id'] as int,
        code: json['code'] as String,
        name: json['name'] as String,
        level: (json['level'] as int?) ?? 1,
      );

  @override
  List<Object?> get props => [id, code];
}

class EmployeeListItem extends Equatable {
  const EmployeeListItem({
    required this.id,
    required this.employeeCode,
    required this.firstName,
    required this.lastName,
    this.photoUrl,
    this.designation,
    this.department,
    this.category,
    required this.isOnProbation,
    required this.status,
    this.dateOfJoining,
  });

  final int id;
  final String employeeCode;
  final String firstName;
  final String lastName;
  final String? photoUrl;
  final Designation? designation;
  final Department? department;
  final EmployeeCategory? category;
  final bool isOnProbation;
  final String status;
  final String? dateOfJoining;

  String get fullName => '$firstName $lastName';

  factory EmployeeListItem.fromJson(Map<String, dynamic> json) =>
      EmployeeListItem(
        id: json['id'] as int,
        employeeCode: json['employee_code'] as String,
        firstName: json['first_name'] as String,
        lastName: json['last_name'] as String,
        photoUrl: json['photo_url'] as String?,
        designation: json['designation'] == null
            ? null
            : Designation.fromJson(json['designation'] as Map<String, dynamic>),
        department: json['department'] == null
            ? null
            : Department.fromJson(json['department'] as Map<String, dynamic>),
        category: json['category'] == null
            ? null
            : EmployeeCategory.fromJson(
                json['category'] as Map<String, dynamic>),
        isOnProbation: (json['is_on_probation'] as bool?) ?? false,
        status: (json['status'] as String?) ?? 'active',
        dateOfJoining: json['date_of_joining'] as String?,
      );

  @override
  List<Object?> get props => [id];
}

class SalaryBreakup extends Equatable {
  const SalaryBreakup({
    required this.templateName,
    required this.isIntern,
    required this.basic,
    required this.hra,
    required this.otherAllowance,
    required this.gross,
    required this.pfEmployee,
    required this.esicEmployee,
    required this.professionalTax,
    required this.totalDeductions,
    required this.netSalary,
    required this.pfEmployer,
    required this.esicEmployer,
    required this.totalCtcMonthly,
    required this.totalCtcAnnual,
    required this.travelExpenseMax,
  });

  final String templateName;
  final bool isIntern;
  final int basic;
  final int hra;
  final int otherAllowance;
  final int gross;
  final int pfEmployee;
  final int esicEmployee;
  final int professionalTax;
  final int totalDeductions;
  final int netSalary;
  final int pfEmployer;
  final int esicEmployer;
  final int totalCtcMonthly;
  final int totalCtcAnnual;
  final int travelExpenseMax;

  factory SalaryBreakup.fromJson(Map<String, dynamic> json) => SalaryBreakup(
        templateName: json['template_name'] as String,
        isIntern: (json['is_intern'] as bool?) ?? false,
        basic: (json['basic'] as int?) ?? 0,
        hra: (json['hra'] as int?) ?? 0,
        otherAllowance: (json['other_allowance'] as int?) ?? 0,
        gross: (json['gross'] as int?) ?? 0,
        pfEmployee: (json['pf_employee'] as int?) ?? 0,
        esicEmployee: (json['esic_employee'] as int?) ?? 0,
        professionalTax: (json['professional_tax'] as int?) ?? 0,
        totalDeductions: (json['total_deductions'] as int?) ?? 0,
        netSalary: (json['net_salary'] as int?) ?? 0,
        pfEmployer: (json['pf_employer'] as int?) ?? 0,
        esicEmployer: (json['esic_employer'] as int?) ?? 0,
        totalCtcMonthly: (json['total_ctc_monthly'] as int?) ?? 0,
        totalCtcAnnual: (json['total_ctc_annual'] as int?) ?? 0,
        travelExpenseMax: (json['travel_expense_max'] as int?) ?? 0,
      );

  @override
  List<Object?> get props => [templateName, totalCtcAnnual];
}

class EmployeeDetail extends Equatable {
  const EmployeeDetail({
    required this.id,
    required this.employeeCode,
    required this.firstName,
    required this.lastName,
    this.photoUrl,
    this.designation,
    this.department,
    this.category,
    required this.isOnProbation,
    required this.status,
    this.dateOfJoining,
    this.probationEndDate,
    this.confirmationDate,
    this.personalEmail,
    this.personalPhone,
    this.salaryTemplateId,
    this.workLocation,
    required this.ctcAnnual,
    this.dateOfBirth,
    this.gender,
    this.bloodGroup,
    this.maritalStatus,
    this.workMode,
    this.employmentType,
    this.reportingTo,
    this.userId,
  });

  final int id;
  final String employeeCode;
  final String firstName;
  final String lastName;
  final String? photoUrl;
  final Designation? designation;
  final Department? department;
  final EmployeeCategory? category;
  final bool isOnProbation;
  final String status;
  final String? dateOfJoining;
  final String? probationEndDate;
  final String? confirmationDate;
  final String? personalEmail;
  final String? personalPhone;
  final int? salaryTemplateId;
  final String? workLocation;
  final num ctcAnnual;
  final String? dateOfBirth;
  final String? gender;
  final String? bloodGroup;
  final String? maritalStatus;
  final String? workMode;
  final String? employmentType;
  final int? reportingTo;
  final int? userId;

  String get fullName => '$firstName $lastName';

  factory EmployeeDetail.fromJson(Map<String, dynamic> json) => EmployeeDetail(
        id: json['id'] as int,
        employeeCode: json['employee_code'] as String,
        firstName: json['first_name'] as String,
        lastName: json['last_name'] as String,
        photoUrl: json['photo_url'] as String?,
        designation: json['designation'] == null
            ? null
            : Designation.fromJson(json['designation'] as Map<String, dynamic>),
        department: json['department'] == null
            ? null
            : Department.fromJson(json['department'] as Map<String, dynamic>),
        category: json['category'] == null
            ? null
            : EmployeeCategory.fromJson(
                json['category'] as Map<String, dynamic>),
        isOnProbation: (json['is_on_probation'] as bool?) ?? false,
        status: (json['status'] as String?) ?? 'active',
        dateOfJoining: json['date_of_joining'] as String?,
        probationEndDate: json['probation_end_date'] as String?,
        confirmationDate: json['confirmation_date'] as String?,
        personalEmail: json['personal_email'] as String?,
        personalPhone: json['personal_phone'] as String?,
        salaryTemplateId: json['salary_template'] == null
            ? null
            : (json['salary_template'] as Map<String, dynamic>)['id'] as int,
        workLocation: json['work_location'] as String?,
        ctcAnnual: num.tryParse('${json['ctc_annual']}') ?? 0,
        dateOfBirth: json['date_of_birth'] as String?,
        gender: json['gender'] as String?,
        bloodGroup: json['blood_group'] as String?,
        maritalStatus: json['marital_status'] as String?,
        workMode: json['work_mode'] as String?,
        employmentType: json['employment_type'] as String?,
        reportingTo: json['reporting_to'] as int?,
        userId: json['user_id'] as int?,
      );

  @override
  List<Object?> get props => [id];
}
