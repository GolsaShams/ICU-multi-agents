# 🏥 ICU Multi-Agent Virtual Assistant

A real-time Intensive Care Unit monitoring system powered by autonomous agents. Built for **BMG 5109 / ELG 6131 — Medical Diagnostic Engineering**, University of Ottawa, Winter 2026.

---

## 📋 Overview

This project implements a **multi-agent system** that autonomously monitors ICU patients, tracks bed availability, manages nurse workloads, and generates real-time alerts when patient conditions deteriorate.

The system features a **Flask REST API** backend with a **Flutter web dashboard** that provides live visualization across three tabs: Patient Monitors, Bed Availability, and Nurse Assignments.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────┐
│              SQLite Database                      │
│   patients │ bed_availability │ nurse_assignments │ alerts
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│              Agent Layer                          │
│  Patient Monitor │ ECG │ Bed Availability │ Nurse │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│         Flask REST API (app.py)                   │
│   /view  │  /beds  │  /nurses  │  /patient/<id>  │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│        Flutter Web Dashboard (main.dart)          │
│   Monitors  │  Bed Availability  │  Nurse Roster  │
└──────────────────────────────────────────────────┘
```

---

## 🤖 Agents

| Agent | File | Description |
|-------|------|-------------|
| **Patient Monitor** | `agents.py` | Tracks HR, SpO₂, Temperature; classifies status as Critical/Warning/Stable |
| **ECG Waveform** | `ecg_agent.py` | Generates realistic ECG waveforms based on heart rhythm type |
| **Bed Availability** | `bed agent.py` | Monitors bed occupancy, tracks admission/discharge dates |
| **Nurse Assignment** | `nurse_agent.py` | Manages nurse workloads, detects overload, triggers backup requests |

### Alert Rules
- **Critical**: HR > 120 or SpO₂ < 85 or Temp > 39.0°C
- **Warning**: HR > 100 or SpO₂ < 90 or Temp > 38.0°C
- **Nurse Overloaded**: ≥ 2 critical patients or ≥ 3 beds assigned

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask, SQLite |
| Frontend | Flutter (Dart) for Web |
| Agents | Python classes with threading |
| Real-time | Auto-refresh every 3 seconds |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Flutter SDK 3.x
- Chrome browser

### 1. Clone the Repository
```bash
git clone https://github.com/GolsaShams/ICU-multi-agents.git
cd ICU-multi-agents
```

### 2. Install Python Dependencies
```bash
pip install flask flask-cors requests
```

### 3. Start the Flask Backend
```bash
cd icu-dashboard
python app.py
```
The server runs on `http://127.0.0.1:5000`

### 4. Start the Flutter Frontend
```bash
cd icu_flutter
flutter pub get
flutter run -d chrome
```
The dashboard opens on `http://localhost:8080`

---

## 📊 Database Schema

| Table | Description |
|-------|-------------|
| `patients` | Real-time vital signs (HR, SpO₂, Temp, rhythm, status) |
| `bed_availability` | Occupancy status, patient names, admission & discharge dates |
| `nurse_assignments` | Nurse roster, assigned beds, shift info, workload level |
| `alerts` | Auto-generated alerts with timestamps |

---

## 📸 Dashboard Features

### Monitors Tab
- Live patient vital signs cards with color-coded status
- Click any card for detailed view with ECG waveform
- Agent Communication Log with real-time alerts

### Bed Availability Tab
- Summary cards (Total / Occupied / Available)
- Occupancy rate progress bar
- Bed grid with patient info and expected discharge dates

### Nurse Assignments Tab
- Workload summary (Normal / High / Overloaded)
- Nurse roster with assigned beds and shift information
- Color-coded workload badges

---

## 📁 Project Structure

```
ICU-multi-agents/
├── icu-dashboard/          # Flask backend
│   └── app.py              # REST API + vitals simulation
├── icu_flutter/            # Flutter frontend
│   └── lib/main.dart       # Dashboard UI (3 tabs)
├── agents.py               # Patient monitoring agent
├── ecg_agent.py            # ECG waveform generation agent
├── bed agent.py            # Bed availability agent
├── nurse_agent.py          # Nurse assignment agent
├── init_db.py              # Database initialization + sample data
├── spo2_agent.py           # SpO₂ monitoring agent
├── orchestrator.py         # Agent orchestration
├── simulation.py           # Vitals simulation engine
└── data_simulator.py       # Data generation utilities
```

---

## 👩‍💻 Author

**Golsa Shams** — University of Ottawa

BMG 5109 / ELG 6131 — Medical Diagnostic Engineering, Winter 2026
