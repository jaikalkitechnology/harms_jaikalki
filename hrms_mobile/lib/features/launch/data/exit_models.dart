/// Exit clearance (asset NOC) and a manager's view of leaving team members.
class AssetClearanceItem {
  const AssetClearanceItem({
    required this.id,
    required this.assetTag,
    required this.name,
    required this.categoryName,
    required this.category,
    this.brand,
    this.model,
    this.returnedAt,
    this.returnCondition,
  });

  final int id;
  final String assetTag;
  final String name;
  final String category;
  final String categoryName;
  final String? brand;
  final String? model;
  final String? returnedAt;
  final String? returnCondition;

  factory AssetClearanceItem.fromJson(Map<String, dynamic> j) =>
      AssetClearanceItem(
        id: j['id'] as int,
        assetTag: j['asset_tag'] as String,
        name: j['name'] as String,
        category: j['category'] as String,
        categoryName: (j['category_name'] as String?) ?? j['category'] as String,
        brand: j['brand'] as String?,
        model: j['model'] as String?,
        returnedAt: j['returned_at'] as String?,
        returnCondition: j['return_condition'] as String?,
      );
}

class AssetClearance {
  const AssetClearance({
    required this.cleared,
    required this.pending,
    required this.returned,
    this.lastWorkingDay,
  });

  final bool cleared;
  final List<AssetClearanceItem> pending;
  final List<AssetClearanceItem> returned;
  final String? lastWorkingDay;

  factory AssetClearance.fromJson(Map<String, dynamic> j) => AssetClearance(
        cleared: (j['cleared'] as bool?) ?? false,
        lastWorkingDay: j['last_working_day'] as String?,
        pending: ((j['pending'] as List?) ?? const [])
            .map((e) => AssetClearanceItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        returned: ((j['returned'] as List?) ?? const [])
            .map((e) => AssetClearanceItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class TeamExit {
  const TeamExit({
    required this.resignationId,
    required this.status,
    required this.employeeName,
    required this.employeeCode,
    required this.assets,
    this.designation,
    this.lastWorkingDay,
  });

  final int resignationId;
  final String status;
  final String employeeName;
  final String employeeCode;
  final String? designation;
  final String? lastWorkingDay;
  final AssetClearance assets;

  factory TeamExit.fromJson(Map<String, dynamic> j) {
    final res = j['resignation'] as Map<String, dynamic>;
    final emp = j['employee'] as Map<String, dynamic>;
    return TeamExit(
      resignationId: res['id'] as int,
      status: (res['status'] as String?) ?? '',
      lastWorkingDay: (res['actual_last_working_day'] ??
          res['proposed_last_working_day']) as String?,
      employeeName: emp['name'] as String,
      employeeCode: emp['employee_code'] as String,
      designation: emp['designation'] as String?,
      assets: AssetClearance.fromJson(j['assets'] as Map<String, dynamic>),
    );
  }
}
