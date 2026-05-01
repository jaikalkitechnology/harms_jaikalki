# Phase 4.5: Super Admin Features (React)

**Duration:** 7-10 days
**Hours:** 70
**Priority:** HIGH
**Depends on:** Phase 4 (Approvals)

---

## Objective

Build Super Admin specific features in React Admin Web - the most powerful tier with full system control.

## Reference

See HRMS_Architecture.md → Section 17 → Super Admin Features

## Deliverables

- ✅ System configuration management
- ✅ Permission catalog (CRUD)
- ✅ Role builder (custom roles)
- ✅ Admin user management with permission assignment
- ✅ Module enable/disable
- ✅ Audit logs viewer
- ✅ White-labeling controls
- ✅ Database backup management
- ✅ API keys management
- ✅ Email/SMS templates

---

## Tasks

### Task 4.5.1: Backend - Super Admin APIs (8h)

**System Config:**
```
GET  /admin/system/config
PUT  /admin/system/config
GET  /admin/system/health
POST /admin/system/backup
GET  /admin/system/backups
POST /admin/system/restore/{backup_id}
```

**Permission Management:**
```
GET    /admin/permissions
POST   /admin/permissions
PUT    /admin/permissions/{id}
DELETE /admin/permissions/{id}

GET    /admin/permissions/categories
```

**Role Management:**
```
GET    /admin/roles
POST   /admin/roles                  # Create custom role
PUT    /admin/roles/{id}
DELETE /admin/roles/{id}
POST   /admin/roles/{id}/permissions # Assign permissions
GET    /admin/roles/{id}/users       # Users with this role
```

**Admin Management:**
```
GET    /admin/admins
POST   /admin/admins                  # Create admin
PUT    /admin/admins/{id}
DELETE /admin/admins/{id}
POST   /admin/admins/{id}/permissions # Set granular permissions
GET    /admin/admins/{id}/audit       # Their actions
```

**Module Management:**
```
GET  /admin/modules
PUT  /admin/modules/{id}/enable
PUT  /admin/modules/{id}/disable
PUT  /admin/modules/{id}/configure
```

**Audit Logs:**
```
GET  /admin/audit-logs
GET  /admin/audit-logs/export
POST /admin/audit-logs/filter
```

**Branding:**
```
GET  /admin/branding
PUT  /admin/branding
POST /admin/branding/logo
```

### Task 4.5.2: Backend - Database Models (4h)

```python
- SystemConfig (id, key, value, category, updated_by, updated_at)
- ModuleSetting (id, module_code, is_enabled, config_json)
- BrandingSettings (id, company_id, logo_url, primary_color, ...)
- DatabaseBackup (id, file_path, size, created_by, created_at, status)
- ApiKey (id, name, key_hash, scopes, expires_at, created_by)
- EmailTemplate (id, code, subject, body_html, variables)
```

### Task 4.5.3: React - System Config Page (5h)

```tsx
// src/features/super-admin/SystemConfig.tsx

Sections:
- General (company name, timezone, currency)
- Email (SMTP settings, test email)
- SMS (provider config)
- Storage (S3/MinIO)
- Database (backups, restore)
- Security (password policy, 2FA settings)
- Notifications (defaults)
```

### Task 4.5.4: React - Permission Catalog (5h)

```tsx
// src/features/super-admin/PermissionCatalog.tsx

Features:
- List all permissions grouped by category
- Search/filter
- Create new permission
- Edit permission
- Delete (with usage check)
- View which roles have it
- Bulk import from CSV
```

### Task 4.5.5: React - Role Builder (8h)

```tsx
// src/features/super-admin/RoleBuilder.tsx

Workflow:
1. Click "Create Role"
2. Enter name, description, level
3. Optional: Inherit from existing role
4. Multi-select permissions (categorized)
5. Preview permissions
6. Save role
7. Optionally assign to users immediately

UI Elements:
- Two-column layout (categories | permissions)
- Search permissions
- Bulk select per category
- Drag-drop reordering
- Visual indication of inherited vs custom
```

### Task 4.5.6: React - Admin User Management (8h)

```tsx
// src/features/super-admin/AdminPermissions.tsx

Features:
- List all admins
- Create new admin (sends invite email)
- Click admin → permission editor
- Permission tree with checkboxes
- Granular control:
  - Module access
  - CRUD operations per entity
  - Report access
  - Configuration access
- Save permissions
- Audit log of permission changes
- Revoke admin access
```

### Task 4.5.7: React - Module Management (4h)

```tsx
// src/features/super-admin/ModuleManagement.tsx

Display:
- Core modules (always enabled)
- Optional modules (toggle on/off)
- Per-module config:
  - Settings JSON
  - Permissions enabled
  - User access

Modules:
☑ Daily Work Planning
☑ Payroll
☑ Justice Portal
☑ Field Force
☐ LMS & Examinations
☐ Trainer Module
☐ Performance Management
```

### Task 4.5.8: React - Audit Logs Viewer (5h)

```tsx
// src/features/super-admin/AuditLogs.tsx

Features:
- Real-time updates (polling or SSE)
- Filters:
  - User
  - Action type
  - Entity
  - Date range
  - IP address
  - Source (web/mobile)
- Search
- Export to Excel/CSV
- Detailed view modal
- Pagination (large datasets)
```

### Task 4.5.9: React - White-Labeling (5h)

```tsx
// src/features/super-admin/Branding.tsx

Customizable:
- Company name
- Logo (with preview)
- Primary color (color picker)
- Secondary color
- Font family
- Login page background
- Email template colors
- Mobile app branding
- Custom domain (if SaaS)

Features:
- Live preview
- Reset to defaults
- Export settings
- Apply across platforms
```

### Task 4.5.10: React - Database Backup (4h)

```tsx
// src/features/super-admin/DatabaseBackup.tsx

Features:
- Schedule automated backups (daily/weekly)
- Manual backup trigger
- List of backups with size
- Download backup
- Restore from backup (with confirmation)
- Retention policy
- Cloud backup (S3) configuration
```

### Task 4.5.11: React - API Keys Management (3h)

```tsx
// src/features/super-admin/ApiKeys.tsx

Features:
- Generate API keys for integrations
- Set scopes/permissions per key
- Expiry date
- Revoke keys
- Usage statistics
- Rate limits per key
```

### Task 4.5.12: React - Email Templates (4h)

```tsx
// src/features/super-admin/EmailTemplates.tsx

Templates:
- Welcome email
- Password reset
- Leave approved/rejected
- Payslip generated
- Birthday wishes
- Custom templates

Editor:
- Rich text editor
- Variable insertion ({{name}}, {{date}})
- Preview with sample data
- Test email send
```

### Task 4.5.13: Tests (5h)

- API endpoints tested
- Permission boundaries verified
- Audit log accuracy
- Role builder workflow
- Module enable/disable

---

## Acceptance Criteria

### Backend
- [ ] Super Admin can CRUD permissions
- [ ] Super Admin can create custom roles
- [ ] Super Admin can assign granular permissions to admins
- [ ] Module enable/disable affects accessibility
- [ ] All actions logged to audit
- [ ] Backup system functional
- [ ] Branding changes apply system-wide

### Frontend
- [ ] All Super Admin pages accessible
- [ ] Role builder UX intuitive
- [ ] Permission tree clear
- [ ] Audit logs filterable
- [ ] Branding live preview
- [ ] Backup download works
- [ ] Email template editor functional

---

## Validation

```bash
# Login as Super Admin
curl -X POST http://localhost:8000/auth/admin/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"super@admin.com","password":"super123"}'

# Create custom role
curl -X POST http://localhost:8000/admin/roles \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "HR Admin",
    "level": 4,
    "permissions": ["employee.create", "employee.view.all"]
  }'

# Assign permissions to admin
curl -X POST http://localhost:8000/admin/admins/2/permissions \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "permissions": ["employee.create", "employee.view.all", "report.team"]
  }'
```

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 17 (Super Admin & Admin Web Portal).

Implement Phase 4.5 (Super Admin Features) as described.

Backend (FastAPI):
1. System config APIs
2. Permission CRUD APIs
3. Role builder APIs
4. Admin permission assignment APIs
5. Module enable/disable
6. Audit log queries
7. Branding APIs
8. Database backup automation
9. API keys management
10. Email template management

React Admin Web (Super Admin only):
1. System Configuration page
2. Permission Catalog manager
3. Role Builder with drag-drop
4. Admin Permission Editor (granular)
5. Module Management toggles
6. Audit Logs viewer with filters
7. White-labeling/Branding tool
8. Database Backup manager
9. API Keys generator
10. Email Template editor

This is the most powerful tier. Test extensively:
- Permission boundaries (Super Admin can do everything)
- Admin restrictions (only granted permissions)
- Audit log captures everything
- Module disable hides UI in mobile app too

Use shadcn/ui components throughout.
Make sure UX is professional and intuitive.
```

---

## Next Phase

➡️ **Phase 5: Mobile App Polish** (existing phase)
