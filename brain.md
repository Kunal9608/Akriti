# 🧠 Akriti Pathology Lab System - Project Brain

**Goal of this file:** This is the core knowledge base (`brain.md`) for the Akriti Pathology Lab Management System. Future AI models should read this file first to understand the project architecture, features, tech stack, and recent implementations without needing to scan the entire codebase.

---

## 🏗️ 1. Project Overview & Architecture
This is a custom-designed Pathology Laboratory Management System for **Akriti Diagnostics Center**. It is designed as a decoupled but unified monolith containing a robust Python API and a lightweight, fast Vanilla JavaScript frontend.

### Directory Structure Pattern
- `/backend`: The core Python API. Follows a strict layered architecture:
  - `app/routers/`: FastAPI endpoint definitions.
  - `app/services/`: Business logic, integrations (WhatsApp, PDFs).
  - `app/repositories/`: Database abstraction layer (Repo pattern) using SQLAlchemy.
  - `app/models/`: SQLAlchemy database schemas.
  - `app/schemas/`: Pydantic models for request/response validation.
  - `app/core/`: Security, config, DB connections.
- `/frontend`: Vanilla HTML5, CSS3, and ES6+ JS. No heavy frameworks (no React/Vue).
  - Uses a custom Design System: Cream Vanilla (`#EFE6DD`) & Cherry Cola (`#9A0002`).
  - Contains `/admin`, `/staff`, and `attendance-kiosk.html`.
- `main.py`: Single root entry point that runs the FastAPI backend and serves the frontend statically.

---

## 🛠️ 2. Technology Stack
- **Backend:** Python 3.10+, FastAPI, Uvicorn/Gunicorn.
- **Database:** PostgreSQL (with `pgvector` for biometrics), Redis (for caching & idempotency).
- **Frontend:** Vanilla HTML/CSS/JS.
- **ORM & Migrations:** SQLAlchemy, Alembic.
- **Integrations:** WASender API (WhatsApp Notifications), Brevo (Emails).
- **Environment:** Docker & Docker Compose for containerized deployment.

---

## 🎯 3. Key Modules & Features

### Reception & Billing
- Fast patient registration generating unique codes (e.g., `PAT260001`).
- Server-side price calculation to prevent frontend tampering.
- **Offline Mode:** Local queueing of data that syncs when the internet is restored.
- **Local UPI QR Payments:** Dynamic VPA-based QR code generation bypassing expensive gateways.

### Lab Operations & Reports
- Pre-seeded Test Catalog (~65 tests).
- Structured Result Entry (parameter-based) or Manual PDF upload.
- Advanced state machine tracking: `sample_collected` -> `sent_to_franchise` -> `under_process` -> `partial_release` -> `report_ready`.
- PDFs are secured with modification logs and SHA-256 hash validation.

### WhatsApp Notifications
- Uses WASender API with Cloudflare bypass strategies.
- Triggers instantly on Registration, Status Updates, and Final Report Release.

### Biometric Attendance Kiosk
- Real-time Face Recognition Check-In/Check-Out.
- Uses liveness gating and PostgreSQL `pgvector` extension to store and query facial vectors.

---

## 🔒 4. Security Implementations (Recent Updates)
- **Password Hashing:** Uses `bcrypt` for secure hashing.
- **Salting & Peppering:** Implements automatic salting alongside a secure server-side Pepper for enhanced security.
- **Password Policies:** Enforces strong password rules. (Note: A recent test `test_passwords.py` ensured that "StrongPassword123!" validation behaves correctly).
- **Migration Trigger:** Features a bcrypt migration trigger for upgrading legacy passwords.
- **API Security:** Standard JWT-based authentication via the `/backend/app/core/` module.

---

## 🤖 5. Instructions for Future AI Models
1. **Understand the Repo Pattern:** If asked to add a database feature, do NOT write DB queries in the routers. Create the Pydantic schema -> update SQLAlchemy model -> write queries in `repositories/` -> handle logic in `services/` -> expose via `routers/`.
2. **Frontend Modifications:** Stick to Vanilla JS. Do NOT add React, Vue, or Tailwind unless explicitly told. Use the existing CSS design tokens.
3. **Database Changes:** Always generate Alembic migrations for any changes to `backend/app/models/`.
4. **Check Existing Logic:** Before implementing new integrations, check `backend/app/services/` (like `patient_service.py` or `test_service.py`) to reuse existing connections or methods.
