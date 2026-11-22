# MediQueue – Smart Hospital Queue & Resource Management System

MediQueue is a full-stack smart hospital management platform engineered to reduce patient waiting times, simplify specialist appointment scheduling, automate digital queue token generation, provide dynamic wait-time estimation, and optimize hospital room and clinical resource utilization.

---

## 🌟 Key Features

### 1. Four Role-Specific Healthcare Portals
- **Hospital Administrator**: Real-time KPI analytics (total volume, cancellations, doctor utilization), Chart.js visual metrics (department influx, 7-day volume trend, resource occupancy), doctor and department management, room allocations, and queue auditing.
- **Specialist Doctor**: Digital clinical desk with prominent **"Call Next Patient"** action, patient cabin management, vital signs recording, diagnosis & prescription generator, and duty availability toggling.
- **Front Desk Receptionist**: Fast walk-in patient registration, daily token generation, appointment check-in, department queue overview, and authorized **Emergency Priority Triage**.
- **Patient Portal**: Live digital token ticket with real-time queue position meter (`#X in line`), dynamic estimated wait time (`~Y mins`), upcoming appointments, and past prescription history.

### 2. Smart Queue Engine
- **Daily Sequential Tokens**: Tokens formatted by department code (e.g., `CARD-001`, `PEDI-005`) generated with database transaction integrity.
- **FIFO with Authorized Emergency Override**: Standard patients advance in First-In-First-Out order; authorized clinical staff can elevate urgent cases to Emergency Priority, placing them at the immediate head of the consultation queue.
- **Dynamic Waiting-Time Calculation**: Computed dynamically based on queue position, doctor average consultation duration, and ongoing cabin consultation status.
- **Resilient Cancellation Handling**: Appointments or tokens cancelled do not break daily token sequencing; queue positions automatically slide up for waiting patients.

### 3. Public Waiting Lobby TV Screen
- High-contrast, full-screen waiting room monitor view (`/queue/display/`).
- Real-time auto-polling every few seconds without page reloads.
- Displays currently serving tokens, cabin room numbers, and the next 4 tokens in queue with emergency highlights.

---

## 🛠 Technology Stack

- **Backend**: Python 3.14+ & Django 5.1
- **Database**: SQLite (ACID-compliant with transactions)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3, Bootstrap Icons
- **Charts**: Chart.js 4.4
- **Real-Time Updates**: Fetch API polling engine (`queue-realtime.js`)

---

## 👥 Demo User Accounts & Passwords

The system comes pre-seeded with realistic demonstration accounts:

| Role | Username | Password | Notes |
|---|---|---|---|
| **Hospital Administrator** | `admin` | `admin123` | Full administrative access & analytics |
| **Specialist Doctor (Cardiology)** | `dr.smith` | `doctor123` | Dr. Alexander Smith (Room 101) |
| **Specialist Doctor (Pediatrics)** | `dr.johnson` | `doctor123` | Dr. Emily Johnson (Room 102) |
| **Front Receptionist** | `receptionist` | `reception123` | Walk-in registration & token desk |
| **Patient (John Doe)** | `patient1` | `patient123` | Has active appointments & prescription |
| **Patient (Jane Roe)** | `patient2` | `patient234` | Has active consultation |

*Note: The login page also includes one-click "Quick Demo Login" buttons for instant credential population during demonstrations.*

---

## 🚀 Windows PowerShell Quick Start Guide

Open **Windows PowerShell** in the project directory (`D:\Medical Project`):

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
*(If script execution is disabled on your system, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` or directly invoke `.\venv\Scripts\python.exe`)*

### 2. Install Dependencies (Already installed)
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 3. Run Database Migrations
```powershell
.\venv\Scripts\python.exe manage.py migrate
```

### 4. Load Demonstration Data
Populate the database with 5 clinical departments, 8 doctors, 20 sample patients, hospital rooms, today's appointments, active queues, and consultation records:
```powershell
.\venv\Scripts\python.exe manage.py seed_data
```

### 5. Run the Automated Test Suite
Verify that all 10 unit and integration tests pass:
```powershell
.\venv\Scripts\python.exe manage.py test
```

### 6. Start the MediQueue Development Server
```powershell
.\venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

### 7. Access the Application in Your Browser
- **Hospital Landing Page**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Live Waiting Lobby TV Display**: [http://127.0.0.1:8000/queue/display/](http://127.0.0.1:8000/queue/display/)
- **Sign In Portal**: [http://127.0.0.1:8000/accounts/login/](http://127.0.0.1:8000/accounts/login/)
- **Patient Self-Registration**: [http://127.0.0.1:8000/accounts/register/](http://127.0.0.1:8000/accounts/register/)
- **Django Super Admin**: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📁 Project Architecture

```
d:\Medical Project\
├── accounts/               # CustomUser model (ADMIN, DOCTOR, RECEPTIONIST, PATIENT), auth & RBAC
├── appointments/           # Slot booking, schedule collision prevention & check-in logic
├── dashboard/              # Role-based dashboards (Admin, Doctor, Receptionist, Patient)
├── doctors/                # Department and DoctorProfile management, schedules, and capacity
├── hospital_resources/     # Consultation rooms, ICU bays, and occupancy tracking
├── patients/               # PatientProfile, medical histories, vitals, and walk-in registration
├── queue_management/       # Atomic token engine, FIFO/emergency queue, consultations, and TV display
├── mediqueue/              # Django core configuration (settings, root urls, wsgi)
├── static/
│   ├── css/mediqueue.css   # Modern healthcare SaaS design system
│   └── js/queue-realtime.js# Real-time polling & dynamic UI logic
├── templates/              # Reusable Django templates with Bootstrap 5
├── requirements.txt        # Python package dependencies
├── manage.py               # Django management script
└── README.md               # Documentation and setup instructions
```
