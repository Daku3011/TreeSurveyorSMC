# 🌳 SMC Tree Census & AI Surveyor

A web application for the Surat Municipal Corporation (SMC) to catalog urban trees with GPS mapping, health assessment, carbon stock calculation, and **AI-powered species identification from photos**.

---

## ✨ Features

- 📸 **AI Tree Recognition**: Upload a tree photo to automatically detect species (English + Gujarati), health condition, and estimated age using OpenRouter / Gemini.
- 📍 **GIS & GPS Mapping**: Tag trees with live coordinates, altitude, and view them on interactive Leaflet maps.
- 🌿 **Eco & Carbon Metrics**: Automatically calculates carbon storage (kg CO₂) and oxygen generation.
- 👥 **Role-Based Portals**:
  - **Surveyors**: Add, edit, and track tree surveys in the field.
  - **Admins**: Verify trees, manage species & surveyors, export data to Excel.

---

## 🚀 Quick Start

### 1. Clone & Setup
```bash
git clone git@github.com:Daku3011/TreeSurveyorSMC.git
cd TreeSurveyorSMC

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
*(Optional: Open `.env` and add your `OPENROUTER_API_KEY` or `GEMINI_API_KEY` for AI photo recognition).*

### 3. Seed Database & Run
```bash
python seed.py
python app.py
```
Open **http://localhost:5000** in your browser.

---

## 🔑 Default Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Admin** | `admin@smc.gov.in` | `Admin@123` |
| **Surveyor** | `surveyor1@smc.gov.in` | `User@123` |

---

## 🛠️ Tech Stack
- **Backend**: Python 3, Flask, SQLAlchemy, SQLite / PostgreSQL
- **Frontend**: HTML5, CSS3, Leaflet.js, Chart.js
- **AI Vision**: OpenRouter API (`google/gemini-2.5-flash` or `openai/gpt-4o-mini`)
