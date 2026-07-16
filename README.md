# Akriti Pathology Lab Management System

A premium, professional, and secure Pathology Laboratory Management System designed for **Akriti Diagnostics Center**. This repository houses both the robust **FastAPI (Python)** backend and the modern, responsive **Vanilla HTML/CSS/JS** frontend, run as a single process for easy setup and operation.

---

## 🌟 Key Features

### 1. Reception & Patient Management
*   **Patient Registration & Billing:** Add, edit, and search patients with auto-generated Patient IDs (`PAT{YY}{seq}`) using a calendar-year sequence.
*   **Billing & Invoicing:** Select multiple tests, calculate discount/GST, and generate unique receipts/invoices.
*   **Dynamic UPI QR Payments:** Instant local UPI QR Code generation via standard VPA (Virtual Payment Address)—no expensive third-party payment gateway integration needed.
*   **Offline Mode:** Registers patients, records payments, and caches receipts locally when the internet is down. Auto-syncs to the live server when online.

### 2. Lab Operations & Reporting
*   **Test Catalog:** Fully pre-seeded catalog with 65 standard diagnostic tests.
*   **Sample Tracking:** Clear stage indicators (Pending, Sample Collected, In Lab, Completed).
*   **Dynamic PDF Reports:** High-quality PDF report generation using **WeasyPrint** and **ReportLab** with digital signature verification.
*   **Version Control & Logs:** Strict report version control with immutable logs capturing every edit and download. Allows for partial report releases (Partial Release Status).

### 3. Face Recognition Attendance Kiosk
*   **Biometric Kiosk:** Real-time face recognition attendance checking (Check-In / Check-Out) for lab staff.
*   **Security Gating:** Staff accounts remain inactive until face registration (liveness, pose, and quality checks) is successfully completed.
*   **Biometric Storage:** Encrypted face embeddings stored securely using PostgreSQL's `pgvector` extension (with CPU-matching Python fallback).

### 4. Admin Analytics & Security Controls
*   **Interactive Dashboard:** Real-time KPI summary widgets (Revenue, Expenses, Net Profit, Patient Volume).
*   **Audit Logging:** Strict, insert-only audit log with cryptographic hash chaining ensuring database tamper-evidence.
*   **Session Management:** Admin controls to view login history and terminate active staff sessions.
*   **Lab Branding Settings:** No-code customization of lab name, address, GSTIN, UPI ID, logo, and theme colors directly from the UI.

---

## 🛠️ Tech Stack

*   **Backend:** FastAPI (Python 3.10+), SQLAlchemy Core/ORM, Uvicorn, Gunicorn
*   **Database:** PostgreSQL (with `pgvector` extension), Redis (caching, rate limiting, and idempotency key replays)
*   **Frontend:** Vanilla HTML5, CSS3, ES6+ Javascript (no heavy frameworks)
*   **Design System:** Cream Vanilla (`#EFE6DD`) & Cherry Cola (`#9A0002`) color palette, Fraunces Display Font (titles), Inter Text Font (UI copy), Custom Toasts/Modals, and skeleton loading states.
*   **PDF Generation:** WeasyPrint (HTML-to-PDF compiler), ReportLab
*   **Server/Deployment:** Nginx, Systemd, Ubuntu Linux, Docker

---

## 📂 Directory Structure

```text
├── backend/
│   ├── alembic/                # Database migrations
│   ├── app/
│   │   ├── models/             # SQLAlchemy schemas
│   │   ├── repositories/       # Database access layers
│   │   ├── routers/            # FastAPI endpoint controllers
│   │   ├── services/           # Business logic & core functions
│   │   ├── config.py           # Configuration loader
│   │   └── main.py             # FastAPI App instance & CORS configuration
│   ├── seed/                   # Database seeding scripts (admin & 65 tests)
│   └── alembic.ini             # Alembic configuration
├── frontend/
│   ├── admin/                  # Administrative screens (Dashboard, Expenses, Audit, Settings)
│   ├── staff/                  # Staff actions (Register Patient, Sample Collection, Settings)
│   ├── assets/
│   │   ├── css/                # Tokenized CSS files (components.css, skeleton.css)
│   │   ├── js/                 # Vanilla JS controllers (patient-form.js, modal.js)
│   │   └── images/             # Icons and visual assets
│   ├── index.html              # Main Landing / Login page
│   ├── attendance-kiosk.html   # Face Recognition Kiosk screen
│   └── manifest.json           # Progressive Web App (PWA) configuration
├── docker-compose.yml          # Container configuration and volume mounts
├── main.py                     # Single Entry Point (Bootstrap checks, auto-migrations, Uvicorn)
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment configuration
└── README.md                   # This file
```

---

## 🚀 Getting Started (Local Setup)

### Prerequisites
Make sure you have the following installed on your machine:
*   Python 3.10 or higher
*   PostgreSQL 14+ (optionally with the `pgvector` extension)
*   Redis Server (optional; in-memory fallback enabled if offline)
*   System dependencies for WeasyPrint (Pango, Cairo, GDK-PixBuf)
    *   *Windows:* Install GTK3 installer
    *   *Ubuntu:* `sudo apt install python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0`

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yourusername/akriti-pathlab.git
    cd akriti-pathlab
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables:**
    *   Copy the `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Open `.env` and fill in your actual PostgreSQL credentials, JWT secret key, and SMTP mail configuration.

5.  **Run the Server:**
    Execute the single root command to verify connectivity, apply migrations, seed the database, and spin up the frontend + backend:
    ```bash
    python main.py
    ```

---

## 🐋 Running with Docker (Recommended)

If you have Docker and Docker Compose installed, you can spin up the entire application stack (FastAPI web server, PostgreSQL database with `pgvector`, and Redis) with a single command. The application will dynamically mount the host code directory as a volume (`.:/app`) to reflect immediate changes during active development.

1. **Prerequisites:**
   Make sure you have Docker and Docker Compose installed on your host system.

2. **Run the application stack:**
   ```bash
   docker compose up --build -d
   ```
   This will:
   * Build the FastAPI web application image (including compiling system dependencies for WeasyPrint).
   * Pull and launch `ankane/pgvector` database and `redis:7-alpine`.
   * Wait for services to be healthy, apply pending migrations, auto-seed the test database, and start the app.

3. **Access the services:**
   * **Main Web App / Kiosk:** [http://localhost:8000](http://localhost:8000)
   * **Swagger API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

4. **Restarting the Stack after Code Changes:**
   Since the `docker-compose.yml` uses volume mounts for code (`.:/app`), changes to HTML/CSS/JS reflect immediately. However, if backend python files change, you need to restart the application container to pick up the reload:
   ```bash
   docker-compose restart web
   ```

5. **Stop the application:**
   ```bash
   docker compose down
   ```

---

## 🔒 Production Deployment Checklist

When deploying to a live VPS (e.g., Hostinger KVM 2 / Ubuntu 24.04 LTS):

1.  **Configure environment variables in `.env`:**
    *   Set `ENVIRONMENT=production` (enforces strict SSL/HTTPS checks).
    *   Set a strong, randomly generated `JWT_SECRET_KEY`.
    *   Update `ALLOWED_ORIGINS` to only allow your domain `https://akritidc.in`.
2.  **Web Server:** Use **Nginx** as a reverse proxy, forwarding requests to **Gunicorn** workers running the FastAPI application.
3.  **Security:**
    *   Obtain a free SSL Certificate from **Let's Encrypt (Certbot)** for HTTPS.
    *   Ensure PostgreSQL roles are configured correctly for the immutable audit logs.
4.  **Process Management:** Run the application via **systemd** service units or **Docker Compose** with Restart Policies (`restart: always`) to keep it alive through crashes and system reboots.

---

## 📜 License
This project is proprietary and built specifically for **Akriti Diagnostics Center**. Unauthorized duplication or distribution is prohibited.
