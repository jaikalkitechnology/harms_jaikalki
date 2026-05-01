# Jaikalki HRMS - Phase-Wise Execution Plan

**Project:** Jaikalki Technology HRMS (Multi-Platform)
**Project Path:** `C:\Users\Shyamveer\PycharmProjects\harms_jaikalki`
**Database:** `db_hrms_jaikalki` (MySQL, password: Love1718)
**Total Duration:** ~26-28 weeks (~7 months)
**Total Hours:** ~1,400 hours
**Stack:** FastAPI + React (Admin) + Flutter (Mobile/Web/iOS) + MySQL + Redis

---

## 🏢 Company Details

```
Company Name: Jaikalki Technology Pvt Ltd
Address: Sh N B1/A Ground Floor, Mahavir Nagar,
         Deepak Hospital, Mira Road,
         Thane-401107, Maharashtra
Employee Code Prefix: JKT (e.g., JKT001, JKT014)
Reference Offer Letter: Pooja Kumawat (JKT014)
```

---

## 🎯 Architecture Overview

**Three Frontends, One Backend:**

```
┌──────────────────────────────┐  ┌────────────────────────────────────┐
│  React Admin Web             │  │  Flutter App (single codebase)      │
│  - Super Admin               │  │  ├─ Android                         │
│  - Admin (configurable)      │  │  ├─ iOS                             │
│                              │  │  └─ Web                             │
│  Tech: React + TS + Tailwind │  │  (Director/HR/Manager/Employee/     │
│        + shadcn/ui           │  │   Field Force/Trainer/Intern)       │
└──────────────────────────────┘  └────────────────────────────────────┘
              ↓                                ↓
              └──────── FastAPI + MySQL ────────┘
                  (db_hrms_jaikalki)
```

---

## 👥 Employee Categories (Jaikalki Specific)

| Category | Salary | Probation | Use Case |
|----------|--------|-----------|----------|
| **Intern** | ❌ Travel expense only | ❌ No probation | Short-term internship |
| **Trainee** | ✅ Full salary | ✅ 6 months | Junior fresh joiners |
| **Permanent** | ✅ Full salary | ✅ 6 months | Regular employees |
| **Contract** | ✅ Salary | ❌ As per contract | Project-based |

### Sample Salary (Trainee L1 - Like Pooja)
- Basic: ₹15,000/month
- HRA: ₹4,500/month
- Other: ₹450/month
- **Gross: ₹19,950/month**
- Net: ₹18,000/month (after PF, ESIC)
- **CTC: ₹22,549/month (₹2,70,588/year)**

---

## 📋 How to Use These Files

### Step 1: Setup Project

Place all these MD files in:
```
C:\Users\Shyamveer\PycharmProjects\harms_jaikalki\hrms_structure\
```

### Step 2: Run Claude Code

```bash
# Open terminal/PowerShell
cd C:\Users\Shyamveer\PycharmProjects\harms_jaikalki

# Start Claude Code
claude

# For each phase, give instruction:
"Read hrms_structure/PHASE_00_Foundation.md and implement everything described.
Reference hrms_structure/HRMS_Architecture.md and hrms_structure/SALARY_STRUCTURE_JAIKALKI.md for full context."
```

---

## 🗂️ All Documentation Files

| File | Purpose |
|------|---------|
| **HRMS_Architecture.md** | Main architecture spec |
| **SALARY_STRUCTURE_JAIKALKI.md** ⭐ NEW | Salary templates, calculations, position categories |
| README.md | This file |

### Phase Files

| Phase | File | Duration | Hours | Tech |
|-------|------|----------|-------|------|
| 0 | [PHASE_00_Foundation.md](./PHASE_00_Foundation.md) | 4 days | 30 | All 3 setup |
| 1 | [PHASE_01_Auth.md](./PHASE_01_Auth.md) | 7 days | 50 | Backend + Flutter |
| 1.5 | [PHASE_01_5_React_Admin_Foundation.md](./PHASE_01_5_React_Admin_Foundation.md) | 7 days | 50 | React Admin |
| 2 | [PHASE_02_Employee.md](./PHASE_02_Employee.md) ⭐ Updated | 7 days | 70 | Backend + Flutter |
| 3 | [PHASE_03_Attendance_Leave.md](./PHASE_03_Attendance_Leave.md) | 10 days | 70 | Backend + Flutter |
| 4 | [PHASE_04_Approvals.md](./PHASE_04_Approvals.md) | 5 days | 50 | Backend + Flutter |
| 4.5 | [PHASE_04_5_Super_Admin.md](./PHASE_04_5_Super_Admin.md) | 10 days | 70 | React Admin |
| 5 | [PHASE_05_Mobile_Polish.md](./PHASE_05_Mobile_Polish.md) | 10 days | 80 | Flutter |
| 6 | [PHASE_06_DWP.md](./PHASE_06_DWP.md) | 7 days | 65 | Backend + Flutter |
| 7 | [PHASE_07_Payroll.md](./PHASE_07_Payroll.md) ⭐ Updated | 14 days | 90 | Backend + Both |
| 8 | [PHASE_08_Justice.md](./PHASE_08_Justice.md) | 10 days | 75 | Backend + Flutter |
| 9 | [PHASE_09_Field_Force_Core.md](./PHASE_09_Field_Force_Core.md) | 14 days | 90 | Backend + Flutter |
| 10-12 | [PHASE_10_11_12_FieldForce_LMS.md](./PHASE_10_11_12_FieldForce_LMS.md) | 25 days | 225 | Backend + Both |
| 13-18 | [PHASE_13_to_18_Final.md](./PHASE_13_to_18_Final.md) | 35 days | 355 | All |

---

## 🔧 Database Configuration (Jaikalki)

```env
# .env file
DATABASE_URL=mysql+aiomysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4
DATABASE_URL_SYNC=mysql+pymysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4

# Company
COMPANY_NAME=Jaikalki Technology Pvt Ltd
EMPLOYEE_CODE_PREFIX=JKT
```

### MySQL Setup

```bash
# Start with Docker (recommended)
docker-compose up -d

# Or manually
mysql -u root -pLove1718
CREATE DATABASE db_hrms_jaikalki CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# Verify
docker exec -it jaikalki_hrms_mysql mysql -u root -pLove1718 db_hrms_jaikalki -e "SHOW DATABASES;"

# phpMyAdmin
# http://localhost:8080
# Username: root
# Password: Love1718
```

---

## 💰 Cost Estimation

### Claude API Cost (Using Claude Code)

| Phase | Approx Code Lines | API Cost |
|-------|-------------------|----------|
| Phase 0 | ~2,500 | $4-5 |
| Phase 1 | ~3,000 | $4-5 |
| Phase 1.5 | ~3,500 | $5-7 |
| Phase 2 | ~5,500 | $7-9 (with Jaikalki templates) |
| Phase 3 | ~5,000 | $7-9 |
| Phase 4 | ~2,500 | $3-4 |
| Phase 4.5 | ~5,000 | $8-10 |
| Phase 5 | ~5,000 | $7-9 |
| Phase 6 | ~3,500 | $5-6 |
| Phase 7 | ~6,500 | $9-12 (with offer letter gen) |
| Phase 8 | ~4,500 | $7-9 |
| Phase 9 | ~5,500 | $8-10 |
| Phase 10-12 | ~12,000 | $18-25 |
| Phase 13-18 | ~16,000 | $25-35 |
| **Total** | **~80,000 lines** | **$120-160** |

**With $50 free credits initially, your out-of-pocket: ~$70-110**

---

## 🚀 Recommended Approach

### Option A: Sequential (Safe) ⭐ RECOMMENDED
Execute one phase at a time, test thoroughly.
- **Time:** 7 months
- **Best for:** Production-ready system

### Option B: MVP First, Then Expand
Phases 0-5 + 1.5 first → Launch MVP → Continue.
- **Time to MVP:** 7-8 weeks

### Option C: Parallel Development
- Backend developer: Phase 1, 2, 3...
- Flutter developer: Phase 1, 2, 3 (after backend)
- React developer: Phase 1.5, 4.5...
- **Time:** 4 months with team of 3

---

## 📝 Important Notes for Implementation

### Salary Calculator Validation

The salary calculator MUST match Pooja's offer letter exactly:

```python
# Input
ctc_annual = 270588

# Expected Output (Jaikalki Trainee L1 template)
{
    "basic": 15000,
    "hra": 4500,
    "other_allowance": 450,
    "gross": 19950,
    "pf_employee": 1800,
    "esic_employee": 150,
    "professional_tax": 0,
    "total_deductions": 1950,
    "net_salary": 18000,
    "pf_employer": 1950,
    "esic_employer": 649,
    "total_ctc_monthly": 22549,
    "total_ctc_annual": 270588
}
```

### Intern Workflow

```
Intern Joins
    ↓
NO Salary Setup (only travel expense)
    ↓
Daily/Weekly Travel Expense Submission
    ↓
HR/Manager Approval
    ↓
Monthly Reimbursement Processing
    ↓
End of Internship → Convert to Trainee (with salary + 6-month probation)
```

### Probation Workflow

```
Trainee/Permanent Joins
    ↓
6-Month Probation Auto-Set
    ↓
Monthly Performance Reviews
    ↓
[At 6 Months]
    ↓
HR Decision:
├─ Confirm → Generate Confirmation Letter → Move to Permanent
├─ Extend → Add 2 more months → Re-evaluate
└─ Terminate → 1 week notice → Exit
```

---

## ✅ Phase 0 Quick Start

```bash
# 1. Open Claude Code
cd C:\Users\Shyamveer\PycharmProjects\harms_jaikalki
claude

# 2. Tell Claude
"Read hrms_structure/HRMS_Architecture.md, hrms_structure/SALARY_STRUCTURE_JAIKALKI.md,
and hrms_structure/PHASE_00_Foundation.md.
Then implement Phase 0 for Jaikalki HRMS as described.
Use database name db_hrms_jaikalki with password Love1718.
Employee code prefix: JKT.
Create three projects: hrms_backend, hrms_admin_web, hrms_mobile."

# 3. Wait for completion, then test
docker-compose up -d
docker exec -it jaikalki_hrms_mysql mysql -u root -pLove1718 -e "SHOW DATABASES;"
```

---

## 🔗 Quick Links

- [Main Architecture Doc](./HRMS_Architecture.md)
- [Salary Structure (Jaikalki)](./SALARY_STRUCTURE_JAIKALKI.md) ⭐ NEW
- [Phase 0 - Foundation](./PHASE_00_Foundation.md)
- [Phase 2 - Employee (with Jaikalki)](./PHASE_02_Employee.md) ⭐ Updated
- [Phase 7 - Payroll (with offer letter)](./PHASE_07_Payroll.md) ⭐ Updated

---

**Document Version:** 3.0 (Jaikalki Edition)
**Created:** April 2026
**Total Phases:** 21 (Phase 0 to Phase 18 + 1.5 + 4.5)
**Reference Offer Letter:** Pooja Kumawat (JKT014) - Jaikalki Technology Pvt Ltd

---

## 📋 How to Use These Files

Each phase file is a standalone instruction set for **Claude Code**. Open Claude Code in your terminal, then for each phase:

```bash
# Open Claude Code
claude

# Tell Claude to read and execute the phase
"Read PHASE_00_Foundation.md and implement everything described.
Reference HRMS_Architecture.md for full context."
```

---

## 🗂️ All Phase Files

| Phase | File | Duration | Hours | Tech |
|-------|------|----------|-------|------|
| 0 | [PHASE_00_Foundation.md](./PHASE_00_Foundation.md) | 4 days | 30 | All 3 setup |
| 1 | [PHASE_01_Auth.md](./PHASE_01_Auth.md) | 7 days | 50 | Backend + Flutter |
| **1.5** | [PHASE_01_5_React_Admin_Foundation.md](./PHASE_01_5_React_Admin_Foundation.md) | 7 days | 50 | **React Admin** |
| 2 | [PHASE_02_Employee.md](./PHASE_02_Employee.md) | 7 days | 60 | Backend + Flutter |
| 3 | [PHASE_03_Attendance_Leave.md](./PHASE_03_Attendance_Leave.md) | 10 days | 70 | Backend + Flutter |
| 4 | [PHASE_04_Approvals.md](./PHASE_04_Approvals.md) | 5 days | 50 | Backend + Flutter |
| **4.5** | [PHASE_04_5_Super_Admin.md](./PHASE_04_5_Super_Admin.md) | 10 days | 70 | **React Admin** |
| 5 | [PHASE_05_Mobile_Polish.md](./PHASE_05_Mobile_Polish.md) | 10 days | 80 | Flutter |
| 6 | [PHASE_06_DWP.md](./PHASE_06_DWP.md) | 7 days | 65 | Backend + Flutter |
| 7 | [PHASE_07_Payroll.md](./PHASE_07_Payroll.md) | 14 days | 90 | Backend + Both |
| 8 | [PHASE_08_Justice.md](./PHASE_08_Justice.md) | 10 days | 75 | Backend + Flutter |
| 9 | [PHASE_09_Field_Force_Core.md](./PHASE_09_Field_Force_Core.md) | 14 days | 90 | Backend + Flutter |
| 10-12 | [PHASE_10_11_12_FieldForce_LMS.md](./PHASE_10_11_12_FieldForce_LMS.md) | 25 days | 225 | Backend + Both |
| 13-18 | [PHASE_13_to_18_Final.md](./PHASE_13_to_18_Final.md) | 35 days | 355 | All |

**New Phases Added:**
- **Phase 1.5:** React Admin Web foundation (auth, layout, components)
- **Phase 4.5:** Super Admin features (system config, permissions, modules)

---

## 🎯 Phase Dependencies

```
Phase 0 (Foundation - 3 projects setup)
    ↓
Phase 1 (Backend Auth + Flutter Auth)
    ↓
Phase 1.5 (React Admin Auth & Foundation) ← NEW
    ↓
Phase 2 (Employee)
    ↓
Phase 3 (Attendance + Leave)
    ↓
Phase 4 (Universal Approvals)
    ↓
Phase 4.5 (Super Admin Features) ← NEW
    ↓
Phase 5 (Mobile Polish) ← MVP READY
    ↓
─── MVP Launch Possible ───
    ↓
Phase 6 → 18 (Continue)
```

---

## 💰 Cost Estimation (Updated)

### Claude API Cost (Using Claude Code)

| Phase | Approx Code Lines | API Cost |
|-------|-------------------|----------|
| Phase 0 | ~2,500 | $4-5 |
| Phase 1 | ~3,000 | $4-5 |
| **Phase 1.5** | **~3,500** | **$5-7** |
| Phase 2 | ~4,500 | $6-8 |
| Phase 3 | ~5,000 | $7-9 |
| Phase 4 | ~2,500 | $3-4 |
| **Phase 4.5** | **~5,000** | **$8-10** |
| Phase 5 | ~5,000 | $7-9 |
| Phase 6 | ~3,500 | $5-6 |
| Phase 7 | ~5,500 | $8-10 |
| Phase 8 | ~4,500 | $7-9 |
| Phase 9 | ~5,500 | $8-10 |
| Phase 10-12 | ~12,000 | $18-25 |
| Phase 13-18 | ~16,000 | $25-35 |
| **Total** | **~78,000 lines** | **$115-150** |

**With $50 free credits initially, your out-of-pocket: ~$65-100**

---

## 🚀 Recommended Approach

### Option A: Sequential (Safe) ⭐ RECOMMENDED
Execute one phase at a time, test thoroughly.
- **Time:** 7 months
- **Best for:** Production-ready system

### Option B: MVP First, Then Expand
Phases 0-5 + 1.5 first → Launch MVP → Continue.
- **Time to MVP:** 7-8 weeks
- **Best for:** Quick validation

### Option C: Parallel Development
- Backend developer: Phase 1, 2, 3...
- Flutter developer: Phase 1, 2, 3 (after backend)
- React developer: Phase 1.5, 4.5...
- **Time:** 4 months with team of 3

---

## 📝 Tips for Claude Code

### Project Structure (Monorepo)

```
hrms_project/
├── docs/
│   ├── HRMS_Architecture.md
│   ├── PHASE_00_Foundation.md
│   ├── PHASE_01_Auth.md
│   ├── PHASE_01_5_React_Admin_Foundation.md
│   ├── PHASE_04_5_Super_Admin.md
│   └── ... (all phase files)
│
├── hrms_backend/         # FastAPI
├── hrms_admin_web/       # React (NEW)
└── hrms_mobile/          # Flutter (Mobile + Web)
```

### Before Starting Each Phase

1. **Read the phase file completely**
2. **Verify previous phase is working**
3. **Run all existing tests**
4. **Backup current code (git commit)**

### During Phase Execution

```bash
# Start with reading specs
"First, read PHASE_XX_Name.md and HRMS_Architecture.md.
Then implement all tasks in order."

# After each major task
"Run the tests and verify they pass."

# If something fails
"The test X is failing. Debug and fix it."
```

### After Each Phase

1. **Run all tests**
2. **Manual testing across all platforms** (mobile, web, admin)
3. **Git commit** with phase number
4. **Update progress** in this README

---

## 🎓 Pro Tips

### 1. Test on All Platforms
- Backend: pytest
- React Admin: Vitest + Cypress
- Flutter: flutter test

### 2. Sync API Changes
When backend changes, update both:
- React types (TypeScript)
- Flutter models (Dart)

### 3. Use Shared Types
Consider OpenAPI generator:
```bash
# Generate TypeScript types from FastAPI OpenAPI
npx openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts

# Generate Dart models
dart pub global activate openapi_generator_cli
openapi-generator generate -i openapi.json -g dart -o lib/api
```

### 4. Use Sonnet for Most, Opus for Critical
- **Sonnet:** Phase 0-6, 9-12 (faster, cheaper)
- **Opus:** Phase 7, 8, 13, 18 (critical: payroll, justice, exams)

### 5. Commit Frequently
```bash
git add .
git commit -m "Phase 1.5.4: React API client implemented"
```

### 6. Test in Production-Like Environment
- Real MySQL (not SQLite)
- Real Redis
- Real S3 (or MinIO)
- Real SSL certificates (Let's Encrypt)

---

## 🔧 Final Project Structure

After all phases:

```
hrms/
├── docs/
│   ├── HRMS_Architecture.md
│   ├── api-docs/                   # OpenAPI generated
│   └── PHASE_00 to PHASE_18.md     # Phase specs
│
├── hrms_backend/                   # FastAPI backend
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── api/v1/                 # Mobile/General APIs
│   │   ├── api/admin/              # Admin-specific APIs
│   │   ├── services/
│   │   └── utils/
│   ├── alembic/
│   ├── tests/
│   ├── requirements.txt
│   └── docker-compose.yml
│
├── hrms_admin_web/                 # React Admin (NEW)
│   ├── src/
│   │   ├── lib/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── super-admin/
│   │   │   ├── admin/
│   │   │   ├── employees/
│   │   │   └── reports/
│   │   ├── hooks/
│   │   └── store/
│   ├── package.json
│   └── vite.config.ts
│
├── hrms_mobile/                    # Flutter (Mobile + Web)
│   ├── lib/
│   │   ├── core/
│   │   ├── features/
│   │   └── shared/
│   ├── web/
│   ├── ios/
│   ├── android/
│   └── pubspec.yaml
│
└── infrastructure/
    ├── kubernetes/
    ├── terraform/
    └── ci-cd/
```

---

## 🌐 Deployment Targets

### Backend
- AWS / GCP / Azure
- Or DigitalOcean droplet
- Or Hetzner VPS

### Database
- AWS RDS (MySQL)
- Or self-hosted with backups

### React Admin Web
- Vercel ⭐ (easiest)
- Netlify
- Cloudflare Pages
- AWS S3 + CloudFront
- Same backend server

### Flutter App
- **Mobile:** Google Play Store, Apple App Store
- **Web:** Same as React (Vercel, Netlify)

---

## ✅ Final Checklist

After all phases complete:

- [ ] All tests passing (90%+ coverage)
- [ ] Backend deployed
- [ ] React Admin deployed
- [ ] Flutter Web deployed
- [ ] Android APK released
- [ ] iOS App Store submitted
- [ ] Documentation complete
- [ ] CI/CD working
- [ ] Backups automated
- [ ] Monitoring active
- [ ] SSL certificates installed
- [ ] Team trained

🎉 **Production-ready Multi-Platform HRMS!**

---

## 🔗 Quick Links

- [Main Architecture Doc](./HRMS_Architecture.md)
- [Phase 0 - Foundation](./PHASE_00_Foundation.md)
- [Phase 1 - Auth (Backend + Flutter)](./PHASE_01_Auth.md)
- [Phase 1.5 - React Admin Foundation](./PHASE_01_5_React_Admin_Foundation.md) ⭐ NEW
- [Phase 4.5 - Super Admin Features](./PHASE_04_5_Super_Admin.md) ⭐ NEW
- [Phase 18 - Final Deployment](./PHASE_13_to_18_Final.md)

---

**Document Version:** 2.0 (Multi-Platform)
**Created:** April 2026
**Total Phases:** 21 (Phase 0 to Phase 18 + 1.5 + 4.5)
