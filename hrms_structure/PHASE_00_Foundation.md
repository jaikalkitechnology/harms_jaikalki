# Phase 0: Project Foundation & Setup - Jaikalki HRMS

**Project:** Jaikalki Technology HRMS
**Project Path:** `C:\Users\Shyamveer\PycharmProjects\harms_jaikalki`
**Database:** `db_hrms_jaikalki`
**Duration:** 3-4 days
**Hours:** 25-30
**Priority:** CRITICAL (Must do first)

---

## Project Directory Structure

```
C:\Users\Shyamveer\PycharmProjects\harms_jaikalki\
├── hrms_structure\              # Documentation (these MD files)
│   ├── HRMS_Architecture.md
│   ├── SALARY_STRUCTURE_JAIKALKI.md
│   ├── PHASE_00_Foundation.md
│   ├── PHASE_01_Auth.md
│   └── ... (all phase files)
│
├── hrms_backend\                # FastAPI Backend
│   ├── app\
│   ├── alembic\
│   ├── tests\
│   ├── requirements.txt
│   ├── docker-compose.yml
│   └── .env
│
├── hrms_admin_web\              # React Admin Panel
│   ├── src\
│   ├── public\
│   ├── package.json
│   └── vite.config.ts
│
└── hrms_mobile\                 # Flutter App (Android/iOS/Web)
    ├── lib\
    ├── android\
    ├── ios\
    ├── web\
    └── pubspec.yaml
```

---

## Objective

Setup the complete project structure for both backend (FastAPI) and mobile (Flutter), with database connections, Docker, and CI/CD foundation.

## Deliverables

By end of this phase:
- ✅ Backend project running on `http://localhost:8000`
- ✅ Health check endpoint working
- ✅ MySQL + Redis connected
- ✅ Flutter project running on emulator
- ✅ Docker Compose for local dev
- ✅ Git repository with proper structure
- ✅ Environment variables configured

---

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLAlchemy 2.0 (async)
- **Validation:** Pydantic v2
- **Migrations:** Alembic
- **Database:** MySQL 8.0+
- **Cache:** Redis 7+
- **Task Queue:** Celery
- **Storage:** S3 / MinIO (local)

### Admin Web (NEW)
- **Framework:** React 18+ with Vite
- **Language:** TypeScript
- **State:** Zustand
- **UI:** shadcn/ui + Tailwind CSS
- **Tables:** TanStack Table
- **Forms:** React Hook Form + Zod
- **HTTP:** Axios
- **Auth:** httpOnly cookies (more secure for web)

### User App (Multi-Platform)
- **Framework:** Flutter 3.x
- **Targets:** Android, iOS, Web (single codebase)
- **State Management:** flutter_bloc
- **Routing:** go_router
- **DI:** get_it
- **HTTP:** dio
- **Local Storage:** flutter_secure_storage

---

## Tasks

### Task 0.1: Backend Project Structure (4h)

Create FastAPI project with this structure:

```
hrms_backend/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI entry
│   ├── config.py              # Settings
│   ├── database.py            # DB session
│   ├── dependencies.py        # Common deps
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── permissions.py
│   │   ├── exceptions.py
│   │   └── middleware.py
│   │
│   ├── models/
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   └── __init__.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   └── v1/
│   │       └── __init__.py
│   │
│   ├── services/
│   │   └── __init__.py
│   │
│   ├── tasks/
│   │   └── __init__.py
│   │
│   └── utils/
│       └── __init__.py
│
├── alembic/
│   └── versions/
├── tests/
│   └── __init__.py
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── .gitignore
└── README.md
```

### Task 0.2: requirements.txt (1h)

```txt
fastapi==0.110.0
uvicorn[standard]==0.27.1
sqlalchemy==2.0.27
alembic==1.13.1
aiomysql==0.2.0
pymysql==1.1.0
cryptography==42.0.2
pydantic==2.6.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.9
redis==5.0.1
celery==5.3.6
boto3==1.34.34
python-dotenv==1.0.1
httpx==0.26.0
pytest==8.0.0
pytest-asyncio==0.23.5
```

### Task 0.3: Database Setup (3h)

- MySQL connection (async via aiomysql)
- SQLAlchemy 2.0 base setup
- Alembic configuration
- Base models class
- Database session dependency
- UTF-8 charset (utf8mb4) for emoji + Hindi support
- InnoDB engine for foreign keys

### Task 0.4: Environment Configuration (2h)

`.env.example`:
```env
# App
APP_NAME=Jaikalki HRMS
DEBUG=true
ENVIRONMENT=development

# Company Info
COMPANY_NAME=Jaikalki Technology Pvt Ltd
COMPANY_ADDRESS=Sh N B1/A Ground Floor, Mahavir Nagar, Deepak Hospital, Mira Road, Thane-401107 Maharashtra
EMPLOYEE_CODE_PREFIX=JKT

# Database (MySQL) - Jaikalki Specific
DATABASE_URL=mysql+aiomysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4
DATABASE_URL_SYNC=mysql+pymysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=jaikalki-hrms-secret-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8080"]

# S3/MinIO
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=hrms-files
```

**Note:** Two DATABASE_URLs because:
- `DATABASE_URL` (aiomysql) - for FastAPI async operations
- `DATABASE_URL_SYNC` (pymysql) - for Alembic migrations (sync only)

**Important:** Database name is `db_hrms_jaikalki` and password is `Love1718` as per project requirement.

### Task 0.5: Docker Compose Setup (3h)

`docker-compose.yml` should include:
- MySQL 8.0 (with utf8mb4 charset)
- Redis 7
- MinIO (S3-compatible storage)
- phpMyAdmin (optional, for DB management)

**Sample docker-compose.yml:**

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: jaikalki_hrms_mysql
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: Love1718
      MYSQL_DATABASE: db_hrms_jaikalki
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql-init:/docker-entrypoint-initdb.d
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
      - --default-authentication-plugin=mysql_native_password

  redis:
    image: redis:7-alpine
    container_name: jaikalki_hrms_redis
    restart: always
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  minio:
    image: minio/minio
    container_name: jaikalki_hrms_minio
    restart: always
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"

  phpmyadmin:
    image: phpmyadmin/phpmyadmin
    container_name: jaikalki_hrms_phpmyadmin
    restart: always
    environment:
      PMA_HOST: mysql
      PMA_PORT: 3306
      MYSQL_ROOT_PASSWORD: Love1718
    ports:
      - "8080:80"
    depends_on:
      - mysql

volumes:
  mysql_data:
  redis_data:
  minio_data:
```

### Task 0.6: Main Application (3h)

`app/main.py`:
- FastAPI instance
- CORS middleware
- Exception handlers
- Health check endpoint
- Lifespan context for startup/shutdown
- Router inclusion

### Task 0.7: Flutter Project Setup (4h)

Create Flutter project with structure:

```
hrms_mobile/
├── lib/
│   ├── main.dart
│   ├── app.dart
│   │
│   ├── core/
│   │   ├── constants/
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   └── app_colors.dart
│   │   ├── network/
│   │   │   ├── dio_client.dart
│   │   │   └── interceptors.dart
│   │   ├── storage/
│   │   │   └── secure_storage.dart
│   │   ├── routing/
│   │   │   └── app_router.dart
│   │   └── di/
│   │       └── injection.dart
│   │
│   ├── features/
│   │   └── (will add per phase)
│   │
│   └── shared/
│       ├── widgets/
│       └── extensions/
│
├── assets/
│   ├── images/
│   └── icons/
├── pubspec.yaml
└── README.md
```

### Task 0.8: Flutter Dependencies (1h)

`pubspec.yaml`:
```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
  dio: ^5.4.0
  get_it: ^7.6.4
  go_router: ^13.0.0
  flutter_secure_storage: ^9.0.0
  cached_network_image: ^3.3.0
  intl: ^0.18.1
  permission_handler: ^11.1.0
  connectivity_plus: ^5.0.2
  shared_preferences: ^2.2.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
  bloc_test: ^9.1.5
  mocktail: ^1.0.3
```

### Task 0.9: Theme & Routing Foundation (3h)

- App theme (light + dark mode)
- Color palette
- Typography
- Initial go_router setup
- GetIt DI initialization

### Task 0.10: Git Setup (2h)

- `.gitignore` for all projects
- README.md with setup instructions
- Initial commit
- GitHub repo creation
- Branch strategy (main, develop, feature/*)

### Task 0.11: React Admin Web Setup (4h)

Create React admin project:

```bash
npm create vite@latest hrms_admin_web -- --template react-ts
cd hrms_admin_web
npm install
```

**Folder structure:**

```
hrms_admin_web/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── lib/
│   │   ├── api/
│   │   ├── utils.ts
│   │   └── constants.ts
│   ├── components/
│   │   ├── ui/             # shadcn components
│   │   ├── layouts/
│   │   ├── shared/
│   │   └── auth/
│   ├── features/
│   │   ├── super-admin/
│   │   ├── admin/
│   │   ├── employees/
│   │   ├── reports/
│   │   └── dashboard/
│   ├── hooks/
│   ├── store/
│   ├── types/
│   └── router/
├── public/
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── vite.config.ts
└── .env
```

### Task 0.12: React Dependencies (1h)

```bash
# Install core dependencies
npm install react-router-dom@6 axios @tanstack/react-query @tanstack/react-table
npm install zustand react-hook-form @hookform/resolvers zod
npm install lucide-react date-fns recharts clsx tailwind-merge

# Install Tailwind + shadcn
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Initialize shadcn
npx shadcn-ui@latest init

# Add commonly used shadcn components
npx shadcn-ui@latest add button input label dialog table form
npx shadcn-ui@latest add dropdown-menu sheet tabs toast card
```

### Task 0.13: React Foundation (3h)

Create:
1. **Auth setup** - Axios interceptors, protected routes
2. **Layout** - AdminLayout with sidebar + header
3. **Router** - All routes defined
4. **API client** - Centralized Axios instance
5. **Login page** - Basic admin login
6. **Dashboard skeleton** - Empty dashboard

### Task 0.14: Flutter Web Configuration (2h)

Configure Flutter project for web support:

```bash
cd hrms_mobile
flutter config --enable-web
flutter create . --platforms=web
```

Update `web/index.html`:
- Custom title
- Meta tags
- App icon

Test web build:
```bash
flutter run -d chrome
flutter build web
```

---

## Acceptance Criteria

### Backend
- [ ] `uvicorn app.main:app --reload` runs without errors
- [ ] `GET http://localhost:8000/health` returns 200
- [ ] `GET http://localhost:8000/docs` shows Swagger UI
- [ ] MySQL container running, can connect
- [ ] phpMyAdmin accessible at http://localhost:8080
- [ ] Redis container running, can ping

### Flutter (Mobile + Web)
- [ ] `flutter run` shows blank app on emulator
- [ ] `flutter run -d chrome` shows app in browser
- [ ] Flutter app has theme applied
- [ ] Builds successfully for Android: `flutter build apk`
- [ ] Builds successfully for Web: `flutter build web`

### React Admin Web
- [ ] `npm run dev` starts on http://localhost:5173
- [ ] React app loads with Tailwind styles
- [ ] shadcn/ui components working
- [ ] Login page renders
- [ ] Builds successfully: `npm run build`

### Common
- [ ] All env variables loaded
- [ ] Git repository initialized with proper structure
- [ ] All 3 projects in single repo (monorepo) or 3 separate repos

---

## Validation Commands

```bash
# Backend
cd hrms_backend
docker-compose up -d  # Starts MySQL, Redis, MinIO
pip install -r requirements.txt
alembic init alembic  # First time only
uvicorn app.main:app --reload

# Test health
curl http://localhost:8000/health

# Test MySQL connection (Jaikalki database)
docker exec -it jaikalki_hrms_mysql mysql -u root -pLove1718 db_hrms_jaikalki -e "SHOW TABLES;"

# phpMyAdmin (browser)
# http://localhost:8080
# Username: root
# Password: Love1718
# Database: db_hrms_jaikalki

# Flutter App (Mobile)
cd hrms_mobile
flutter pub get
flutter run                     # Auto-detect device
flutter run -d chrome           # Run on web

# Build for different platforms
flutter build apk               # Android
flutter build web               # Web
# flutter build ios             # iOS (Mac only)

# React Admin Web
cd hrms_admin_web
npm install
npm run dev                     # http://localhost:5173
npm run build                   # Production build
npm run preview                 # Preview production build
```

---

## ⚠️ MySQL-Specific Notes

### Important Differences from PostgreSQL

If you're familiar with PostgreSQL, note these MySQL differences:

| Feature | PostgreSQL | MySQL |
|---------|-----------|-------|
| JSON type | JSONB (binary) | JSON (text-based) |
| Arrays | ARRAY type | Use JSON or separate table |
| Boolean | BOOLEAN | TINYINT(1) |
| UUID | Native UUID | Use CHAR(36) or BINARY(16) |
| Sequences | SEQUENCE | AUTO_INCREMENT |
| Full-text search | tsvector | FULLTEXT index |
| Case sensitivity | Case-sensitive | Case-insensitive (default) |

### SQLAlchemy Configuration

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Async engine for FastAPI
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # Important for MySQL!
    pool_recycle=3600,   # Recycle connections every hour
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()
```

### Alembic Configuration

```python
# alembic/env.py - use SYNC URL for migrations
from app.config import settings

config.set_main_option("sqlalchemy.url", settings.DATABASE_URL_SYNC)
```

### Common MySQL Settings

In `app/config.py`:

```python
# MySQL-specific table args for new models
mysql_table_args = {
    'mysql_engine': 'InnoDB',
    'mysql_charset': 'utf8mb4',
    'mysql_collate': 'utf8mb4_unicode_ci',
}
```

In your models:

```python
class User(Base):
    __tablename__ = 'users'
    __table_args__ = mysql_table_args  # Apply to all tables

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    # ...
```

### Index Length Issue (Important!)

MySQL has a key length limit. For VARCHAR columns used in indexes:

```python
# ❌ This may fail in MySQL
email = Column(String(500), unique=True)

# ✅ Use 255 or less for indexed columns
email = Column(String(255), unique=True)

# ✅ Or specify index length
__table_args__ = (
    Index('ix_email', 'email', mysql_length=191),
)
```

### JSON Column Usage

```python
# MySQL 8.0+ supports JSON natively
from sqlalchemy import JSON

class Settings(Base):
    config = Column(JSON)  # Works in MySQL 8.0+
```

### Common Issues & Fixes

**Issue 1: "Can't connect to MySQL"**
```bash
# Check if MySQL container is up
docker ps
# Check logs
docker logs hrms_backend_mysql_1
```

**Issue 2: "MySQL server has gone away"**
```python
# Add to engine config
pool_pre_ping=True
pool_recycle=3600
```

**Issue 3: "Specified key was too long"**
```python
# Use shorter VARCHAR for indexes
String(191)  # Safe for utf8mb4
```

**Issue 4: Emoji/Hindi not saving**
```yaml
# In docker-compose.yml MySQL service:
command:
  - --character-set-server=utf8mb4
  - --collation-server=utf8mb4_unicode_ci
```

---

## Claude Code Prompt

```
Read the full HRMS_Architecture.md and SALARY_STRUCTURE_JAIKALKI.md documents.
Pay special attention to:
- Section 17 (Super Admin & Admin Web Portal - React)
- Section 18 (Flutter Multi-Platform Setup)
- Section 2 (Three-Tier Role Architecture)
- SALARY_STRUCTURE_JAIKALKI.md (entire file)

PROJECT CONTEXT:
- Company: Jaikalki Technology Pvt Ltd
- Project Path: C:\Users\Shyamveer\PycharmProjects\harms_jaikalki
- Database: db_hrms_jaikalki
- DB Password: Love1718
- Employee Code Prefix: JKT (e.g., JKT001, JKT014)

Then implement Phase 0 (Foundation) as described in PHASE_00_Foundation.md.

Create THREE projects in the project directory:

1. **hrms_backend/** (FastAPI)
   - Complete project structure
   - docker-compose.yml with MySQL 8.0 (database: db_hrms_jaikalki)
   - MySQL root password: Love1718
   - requirements.txt with aiomysql + pymysql
   - Health endpoint
   - Async SQLAlchemy with MySQL
   - Alembic configured
   - .env with Jaikalki specific values:
     * DATABASE_URL=mysql+aiomysql://root:Love1718@localhost:3306/db_hrms_jaikalki?charset=utf8mb4
     * COMPANY_NAME=Jaikalki Technology Pvt Ltd
     * EMPLOYEE_CODE_PREFIX=JKT

2. **hrms_admin_web/** (React + TypeScript)
   - Vite + React 18 + TypeScript
   - Tailwind CSS + shadcn/ui setup
   - All dependencies installed
   - Folder structure (super-admin, admin, employees, reports)
   - Basic AdminLayout with Sidebar
   - Login page skeleton
   - Axios client with interceptors
   - React Router v6 setup
   - Branding: "Jaikalki HRMS"

3. **hrms_mobile/** (Flutter Multi-Platform)
   - Standard Flutter project
   - Web support enabled
   - All dependencies (bloc, dio, get_it, go_router)
   - Theme + routing foundation
   - Builds for Android, iOS (config), and Web
   - App name: "Jaikalki HRMS"

IMPORTANT for MySQL:
- Database name: db_hrms_jaikalki
- Root password: Love1718
- Use utf8mb4 charset (for emoji + Hindi support)
- aiomysql for async operations
- pymysql for Alembic migrations
- VARCHAR(191) max for indexed columns

IMPORTANT for React:
- TypeScript strict mode
- Axios with httpOnly cookies (for admin auth security)
- Initialize shadcn/ui properly
- Add base components: button, input, dialog, table, form
- Brand as "Jaikalki HRMS"

IMPORTANT for Flutter:
- Enable web platform: `flutter config --enable-web`
- Test on Chrome before completing
- App name: "Jaikalki HRMS"
- Configure web/index.html

Make sure all 3 projects run without errors:
- Backend: http://localhost:8000
- React Admin: http://localhost:5173
- Flutter Web: http://localhost:8081 (or whichever port)

Verify database connection:
docker exec -it jaikalki_hrms_mysql mysql -u root -pLove1718 db_hrms_jaikalki -e "SHOW DATABASES;"

Commit each project structure to git separately.
```

---

## Next Phase

➡️ **Phase 1: Authentication & RBAC** (PHASE_01_Auth.md)
