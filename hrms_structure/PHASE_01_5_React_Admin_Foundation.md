# Phase 1.5: React Admin Web - Auth & Foundation

**Duration:** 5-7 days
**Hours:** 50
**Priority:** CRITICAL
**Depends on:** Phase 1 (Backend Auth)

---

## Objective

Build the React Admin Web app with authentication, layout, role-based routing, and core foundation features for Super Admin and Admin users.

## Reference

See HRMS_Architecture.md → Section 17: Super Admin & Admin Web Portal

## Deliverables

- ✅ React admin login (httpOnly cookies)
- ✅ Super Admin & Admin role detection
- ✅ Protected routes
- ✅ AdminLayout with sidebar + header
- ✅ Permission-based UI rendering
- ✅ Theme (light + dark mode)
- ✅ Toast notifications
- ✅ Error boundary
- ✅ Loading states

---

## Tasks

### Task 1.5.1: Backend - Admin Auth Endpoints (4h)

Add to existing auth module:

```
POST /auth/admin/login          # Admin login (cookie-based)
POST /auth/admin/logout         # Clear cookie
GET  /auth/admin/me             # Current admin info
POST /auth/admin/refresh        # Refresh session
```

**Differences from mobile auth:**
- Use httpOnly cookies (not JWT in body)
- CSRF protection
- Shorter session timeout (8 hours vs 30 days)
- Force 2FA for Super Admin

### Task 1.5.2: Backend - Permission API (4h)

```
GET  /admin/permissions           # All permissions (Super Admin)
GET  /admin/me/permissions        # My permissions
GET  /admin/users/{id}/permissions # User permissions
```

### Task 1.5.3: React - Setup & Configuration (3h)

**Configure Tailwind:**

```js
// tailwind.config.ts
export default {
  content: ['./src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: { /* shadcn variables */ },
      }
    }
  },
  plugins: [require('tailwindcss-animate')],
}
```

**Configure Vite:**

```ts
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    }
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
})
```

### Task 1.5.4: React - API Client (3h)

```typescript
// src/lib/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,  // Send cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - CSRF token
apiClient.interceptors.request.use((config) => {
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken;
  }
  return config;
});

// Response interceptor - handle 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Try refresh
      try {
        await apiClient.post('/auth/admin/refresh');
        return apiClient.request(error.config);
      } catch {
        // Force logout
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### Task 1.5.5: React - Auth Store (Zustand) (3h)

```typescript
// src/store/authStore.ts
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  permissions: string[];
  role: 'super_admin' | 'admin' | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  permissions: [],
  role: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (email, password) => {
    const response = await apiClient.post('/auth/admin/login', {
      email, password
    });
    set({
      user: response.data.user,
      permissions: response.data.permissions,
      role: response.data.role,
      isAuthenticated: true,
    });
  },

  logout: async () => {
    await apiClient.post('/auth/admin/logout');
    set({ user: null, permissions: [], role: null, isAuthenticated: false });
  },

  checkAuth: async () => {
    try {
      const response = await apiClient.get('/auth/admin/me');
      set({
        user: response.data.user,
        permissions: response.data.permissions,
        role: response.data.role,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch {
      set({ isAuthenticated: false, isLoading: false });
    }
  },

  hasPermission: (permission: string) => {
    const { role, permissions } = get();
    if (role === 'super_admin') return true;  // Super Admin has all
    return permissions.includes(permission);
  },
}));
```

### Task 1.5.6: React - Protected Routes (2h)

```tsx
// src/components/auth/ProtectedRoute.tsx
export function ProtectedRoute({ children, requireRole }: Props) {
  const { isAuthenticated, role, isLoading } = useAuthStore();

  if (isLoading) return <LoadingScreen />;
  if (!isAuthenticated) return <Navigate to="/login" />;
  if (requireRole && role !== requireRole) return <Navigate to="/unauthorized" />;

  return <>{children}</>;
}
```

### Task 1.5.7: React - Login Page (4h)

Features:
- Email + password fields
- Form validation (Zod)
- Show/hide password
- Remember me
- Loading state
- Error display
- 2FA prompt (for Super Admin)

```tsx
// src/features/auth/LoginPage.tsx
const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});

export function LoginPage() {
  const form = useForm({
    resolver: zodResolver(loginSchema),
  });
  const { login } = useAuthStore();

  // ... form implementation with shadcn components
}
```

### Task 1.5.8: React - AdminLayout (4h)

```tsx
// src/components/layouts/AdminLayout.tsx
export function AdminLayout() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

### Task 1.5.9: React - Sidebar Navigation (4h)

Role-based menu:

```tsx
const SIDEBAR_ITEMS = {
  super_admin: [
    { icon: Settings, label: 'System', path: '/system' },
    { icon: Shield, label: 'Permissions', path: '/permissions' },
    { icon: Users, label: 'Roles', path: '/roles' },
    { icon: UserCog, label: 'Admin Users', path: '/admins' },
    { icon: Package, label: 'Modules', path: '/modules' },
    { icon: Activity, label: 'Audit Logs', path: '/audit' },
    { icon: Palette, label: 'Branding', path: '/branding' },
    // ... + all admin items
  ],
  admin: [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
    { icon: Users, label: 'Employees', path: '/employees' },
    { icon: Building, label: 'Departments', path: '/departments' },
    { icon: BadgeCheck, label: 'Designations', path: '/designations' },
    { icon: Calendar, label: 'Holidays', path: '/holidays' },
    { icon: Clock, label: 'Shifts', path: '/shifts' },
    { icon: FileText, label: 'Reports', path: '/reports' },
  ],
};
```

### Task 1.5.10: React - Header (3h)

- Logo
- Search bar (global search)
- Notification bell
- Theme toggle (light/dark)
- User dropdown (profile, logout)
- Breadcrumbs

### Task 1.5.11: React - Permission Component (2h)

```tsx
// src/components/shared/PermissionGate.tsx
interface Props {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
}

export function PermissionGate({ permission, children, fallback }: Props) {
  const { hasPermission } = useAuthStore();

  if (!hasPermission(permission)) {
    return fallback || null;
  }

  return <>{children}</>;
}

// Usage:
<PermissionGate permission="employee.create">
  <Button>Add Employee</Button>
</PermissionGate>
```

### Task 1.5.12: React - DataTable Component (5h)

Reusable table component:

```tsx
// src/components/shared/DataTable.tsx
import { useReactTable } from '@tanstack/react-table';

export function DataTable<TData>({
  columns,
  data,
  pagination,
  onRowClick,
  loading,
}: DataTableProps<TData>) {
  // Implementation with TanStack Table
  // - Sorting
  // - Filtering
  // - Pagination
  // - Row selection
  // - Column visibility
}
```

### Task 1.5.13: React - Theme System (2h)

- Light theme (default)
- Dark theme
- System preference detection
- Persist in localStorage
- Smooth transitions

### Task 1.5.14: React - Toast Notifications (1h)

Use `sonner` or shadcn toast:

```tsx
import { toast } from 'sonner';

toast.success('Employee created successfully');
toast.error('Failed to delete user');
```

### Task 1.5.15: React - Error Boundary (1h)

```tsx
// src/components/ErrorBoundary.tsx
export class ErrorBoundary extends Component {
  // Catch errors, show friendly UI
}
```

### Task 1.5.16: React - Loading States (1h)

- Skeleton loaders
- Spinner
- Progress bars
- Suspense boundaries

### Task 1.5.17: Tests (3h)

- Component tests
- Auth flow tests
- Permission tests

---

## Acceptance Criteria

- [ ] Login works with cookies (not localStorage)
- [ ] Super Admin sees all sidebar items
- [ ] Admin sees only granted items
- [ ] Permission gate hides unauthorized buttons
- [ ] Logout clears session
- [ ] Refresh token works
- [ ] Theme toggle works
- [ ] DataTable component reusable
- [ ] Mobile responsive (sidebar collapses)
- [ ] All routes protected
- [ ] 401 redirects to login

---

## Validation

```bash
# Run React app
cd hrms_admin_web
npm run dev
# Open http://localhost:5173

# Run backend
cd hrms_backend
uvicorn app.main:app --reload

# Test login
curl -X POST http://localhost:8000/auth/admin/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"email":"super@admin.com","password":"super123"}'

# Test authenticated endpoint
curl http://localhost:8000/auth/admin/me \
  -b cookies.txt
```

---

## Claude Code Prompt

```
Read HRMS_Architecture.md Section 17 (Super Admin & Admin Web Portal).

Implement Phase 1.5 (React Admin Foundation) as described in PHASE_01_5_React_Admin_Foundation.md.

Backend changes:
1. Add admin auth endpoints with httpOnly cookies
2. CSRF protection for admin routes
3. Force 2FA for Super Admin
4. Permission listing API

React Admin Web:
1. Setup Axios with cookie-based auth
2. Zustand auth store
3. Protected routes
4. AdminLayout with Sidebar + Header
5. Role-based navigation menu
6. Permission gate component
7. Reusable DataTable with TanStack
8. Theme system (light + dark)
9. Toast notifications
10. Error boundary
11. Login page with form validation

Test full flow:
- Super Admin logs in → sees all menu
- Admin with limited permissions → sees subset
- Logout works
- Session refresh works
- Permission gates hide unauthorized UI

Make sure mobile responsive and accessible.
```

---

## Next Phase

➡️ Continue with **Phase 2: Employee Management** (now needs both Flutter mobile + React admin)
