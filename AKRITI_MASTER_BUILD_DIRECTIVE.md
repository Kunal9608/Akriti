# BUILD DIRECTIVE — Akriti Diagnostics Center Pathology Lab Management System

You are given two attached specification documents:
1. **`AKRITI_SRS_v4.md`** — the Software Requirements Specification (what the system must do: every feature, database table, API endpoint, security rule, and UI/design-system rule, with numbered FR/NFR IDs)
2. **`AKRITI_SDD_v1.md`** — the Software Design Document (how it must be built: folder structure, module/class breakdown, algorithms in pseudocode, sequence flows, deployment design)

**Treat both documents as the single source of truth.** Do not invent your own architecture, folder layout, schema, or feature set where these documents already specify one. Where something is ambiguous or not covered, make the most sensible production-grade choice and note the assumption in your output — but do not contradict anything already specified.

Build the **complete, fully working system** — not a scaffold, not placeholder pages, not "TODO" stubs for core features. Implement every module end-to-end: database, backend API, and frontend UI, wired together and runnable.

---

## Non-Negotiable Constraints (do not miss these — common failure points)

- **Tech stack:** FastAPI (Python) backend, PostgreSQL (+ `pgvector` extension) database, plain HTML/CSS/vanilla JS frontend (no React/Vue/Angular). SQLAlchemy + Alembic for schema/migrations. Redis for idempotency keys, rate limiting, and caching. No Docker — deploy directly via Gunicorn/Uvicorn + Nginx as described in the SDD; do not containerize unless asked later.
- **No payment gateway integration of any kind.** UPI QR codes are generated locally from the lab's own VPA string — no Razorpay/Paytm/etc. API calls, no transaction verification service.
- **Notifications:** Email only for now (via `fastapi-mail`, Gmail SMTP with App Password, sender `kunaldixit.2995@gmail.com`, display name "Akriti Diagnostics Center"). Build the notification layer as a provider-abstraction (interface + registry) so WhatsApp/SMS providers can be added later as new classes — never hardcode email-sending logic inline wherever a notification is triggered.
- **Patient ID generation** must use a real PostgreSQL sequence per calendar year (`nextval()`), never `MAX(id)+1` in application code — format `PAT{YY}{seq, min 4 digits}` (e.g. `PAT260001`, `PAT261000`).
- **Idempotency-Key header is mandatory** on every state-changing endpoint (Add/Edit Patient, Attendance check-in/out, Payments, Staff creation, Expense entry) — implement the Redis-backed replay logic exactly as described in the SDD, so double-clicks, retries, and offline-sync replays never create duplicate records.
- **Staff accounts cannot become active until face registration completes** (minimum required embedding samples captured, quality/liveness checks passed) — this is a hard server-side gate, not just a UI step.
- **Immutable audit log:** the `audit_logs` table must be enforced as insert-only at the database role/permission level (not just application logic), with the hash-chaining scheme from the SDD — verify this with an actual permissions test, not just code review.
- **Admin has every capability Staff has**, plus administrative-only features — Admin can register/edit patients, collect payments, upload reports, print receipts, update sample status, and search, in addition to staff management, tests, revenue, expenses, and audit logs.
- **No Patient Portal. No Doctor login/module.** Doctors exist only as a simple reference list used during patient registration.

---

## UI/UX — Follow Exactly, This Is Frequently Under-Implemented

- **Brand colors (mandatory, exact hex):** Cream Vanilla `#EFE6DD` as the dominant light-theme background/surface color, Cherry Cola `#9A0002` as the primary/accent color used sparingly (buttons, active nav indicator, key highlights) — never as a large background fill. Full token table, dark-theme variant, and semantic colors (success/warning/info/error) are specified in SRS §6.1.2 — implement exactly those values, don't substitute a generic Bootstrap/Tailwind default palette.
- **Font pairing (mandatory):** **Fraunces** (Google Fonts) for page titles, panel/section headings, KPI figures, brand name, and modal titles; **Inter** for everything else (tables, forms, buttons, badges, toasts, meta text) — see SRS §6.1.3. Do not use a single generic sans-serif for the whole UI; the display/body pairing is part of the brand identity.
- **Modern, professional, premium, minimalist look** — generous white space, restrained color use, soft shadows instead of heavy borders, typography-led hierarchy. Must not look like a generic open-source admin template.
- **Zero emojis anywhere.** All icons are SVG, one consistent set, theme-aware via `currentColor`.
- **No native browser `alert()`, `confirm()`, or `prompt()` anywhere** — build the custom toast and modal components specified in SRS §6.1.6 and use them for every confirmation/feedback moment in the app.
- **Skeleton loading is mandatory on every data-driven view** — dashboards, tables, charts, pre-filled edit forms, the attendance kiosk, and timeline views must all show shape-matching skeleton placeholders (per SRS §6.1.5) while data loads — never a blank page, a bare spinner, or content that pops in and shifts the layout.
- Fully responsive: phone (card-based stacked tables), tablet (primary staff-use size, 2-column forms), desktop (full multi-column dashboard, persistent sidebar).

---

## Build Order (follow the SDD's suggested sequence)

1. Database schema (all tables from SRS §4, including the v4 additions — expenses, attendance, attendance_logs, face_embeddings, sample_tracking, report_versions, report_download_logs, active_sessions, login_history, lab_settings) + Alembic migrations + seed script (admin account, 65 tests).
2. Auth system: login, email-OTP, forced password reset, password policy, JWT + httpOnly cookies, lockouts, rate limiting.
3. Staff management + mandatory multi-sample face registration flow (liveness/blur/pose checks, encrypted embeddings only, no permanent raw image storage).
4. Face Recognition Attendance (real-time matching via `pgvector`, check-in/out logic, low-confidence fallback, attendance dashboard with Present/Absent/Late/Early Leave/Overtime).
5. Test catalog + Patient Add/Edit (Admin & Staff) with Patient ID generation, multi-test billing, Cash/QR payment logic, receipt/invoice numbering (`RC`, `INV`, `EXP`, `ATT` series per SRS).
6. Patient Overview (shared, view-scope enforced) with search, filters, pagination, and Patient Timeline.
7. Reports module: upload/generate, digital signature, verification hash, report version control.
8. Revenue + Expense modules with net profit/loss, full Dashboard KPI suite, analytics with export (PDF/Excel/CSV).
9. Login History, Active Sessions, Immutable Audit Log viewer.
10. Offline mode (Service Worker + IndexedDB queue) with auto-sync + conflict/duplicate prevention for Patient Registration, Payments, Receipts, and Attendance.
11. Lab Settings module (no-code-change configurable branding: name, logo, GSTIN, UPI ID, footers, theme, etc.).
12. Global Search, Notification-provider abstraction, full security hardening pass (CAPTCHA, CSP, CORS, CSRF, backups, monitoring) before considering it launch-ready.

---

## Setup Automation, Single Entry Point, and Deployment-Readiness (Mandatory)

**Single entry point at the project root:**
- Since the frontend is plain HTML/CSS/vanilla JS (no build step required), architect the FastAPI app to **serve the frontend static files directly** (via `StaticFiles`/Jinja mount) from the same process that serves the API — this means one process, one command, one port, runs everything together. Do not build a separate frontend dev server that needs to run alongside the backend.
- Place a **`main.py` at the project root** (not buried inside `backend/app/`) that is the single command to start the entire system: `python main.py`. It should start the Uvicorn server hosting both the API (under `/api/v1/...`) and the static frontend (served at `/`), with host/port configurable via environment variables (default `0.0.0.0:8000` for local use).
- `main.py` should also run startup checks/bootstrap on launch (e.g. verify DB connectivity, apply any pending Alembic migrations automatically on first run if configured to do so, confirm Redis connectivity) and print a clear success message with the local URL to open once ready.

**Automatic dependency setup:**
- Provide a complete `requirements.txt` (backend) with pinned versions.
- Provide a one-time setup script (e.g. `setup.py` or a small cross-platform `setup` script) that: creates a virtual environment if one doesn't exist, installs everything from `requirements.txt`, prompts for or reads `.env` values, and applies database migrations + runs the seed script — so a non-technical person only has to run this once before using `python main.py` from then on. Do not require anyone to manually figure out and type individual `pip install` commands for each library.
- All dependencies (backend Python packages; any minimal frontend JS libraries used, e.g. a QR-generation library or Chart.js) must be either bundled locally in the project or fetched automatically by the setup step — nothing should require the person running this to hunt down and manually download files themselves.

**`SETUP.txt` (mandatory deliverable, project root):**
Create a plain-text `SETUP.txt` file at the project root, written in simple, non-technical language, covering:
1. What to install first (Python version, PostgreSQL, Redis) and where to get them.
2. Exactly what command(s) to run once, in order, to set everything up (env creation, dependency install, `.env` configuration with a description of each value from the SRS Appendix B list, DB migration, seeding).
3. The single command to start the system afterward every time: `python main.py`.
4. What URL to open in a browser once it's running.
5. How to stop the system safely.
6. A short "Common Problems" section (e.g. port already in use, PostgreSQL not running, missing `.env` value) with plain-language fixes.

**Deployment-readiness (build for this now, even though not deploying yet):**
- No hardcoded `localhost`/`127.0.0.1` URLs anywhere in frontend JS — the frontend must call the API via relative paths (e.g. `/api/v1/...`) so the exact same codebase works unmodified whether accessed at `localhost:8000` today or `https://labs.akritidiagnostics.com` later.
- CORS allowed-origins, database connection string, mail credentials, JWT secret, and every other environment-sensitive value must come from `.env`/environment variables only — never hardcoded — so moving from local machine to a live server is purely a configuration change, not a code change.
- Cookies (JWT access/refresh) must be set with `Secure` conditionally based on environment (allow non-HTTPS locally for development, but the code path for production must enforce `Secure`/HTTPS — document this switch clearly via an environment variable such as `ENVIRONMENT=development|production`).
- Structure the project so it can later sit behind Nginx with a real domain and TLS certificate (e.g. via Let's Encrypt/Certbot) exactly as described in the SDD's deployment diagram, without restructuring — this should already be true if the above points are followed, not something to retrofit later.
- Include a short section in `SETUP.txt` (or a separate `DEPLOYMENT_NOTES.txt`) outlining, at a high level, what changes when moving to a live domain later: pointing `.env` to the production database, setting `ENVIRONMENT=production`, configuring Nginx + a real domain + TLS, and updating the CORS allowed-origin to the live domain.

---



---

## Deliverable Expectations

- Fully working, runnable project (backend + frontend), not partial scaffolding.
- **`main.py` at the project root** as the single command (`python main.py`) to launch the entire system — API and frontend together, one process.
- **`SETUP.txt` at the project root** exactly as described above — clear, plain-language, one-time setup steps plus the everyday run command.
- Clear separation per the SDD folder structure (routers/services/repositories/models on the backend; pages/components/assets on the frontend) — `main.py` at the root simply wires these together and starts the server, it does not contain business logic itself.
- `.env.example` with every required variable, no real secrets committed.
- Working Alembic migrations + seed script, invoked automatically by the setup script.
- The UI must come out looking and functioning like a **premium, professional product built for daily real-world use** — not a rough first draft. Every screen should feel intentional, fast, and genuinely usable by lab counter staff under time pressure: correct brand colors, skeleton loading, no native alerts, clean responsive layout, and SVG iconography exactly as specified — treat the UI/UX section above as equally mandatory as the backend logic, not a cosmetic afterthought to be rushed at the end.

This system will be used daily by a real diagnostic lab's staff and its owner — build it with the correctness, validation, and care that real patient and financial data requires.
