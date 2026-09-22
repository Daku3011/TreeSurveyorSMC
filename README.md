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

#### Choose Your Database:
- **SQLite (Zero Setup - Default)**:
  ```env
  DATABASE_URL=sqlite:///smc_tree_census.db
  ```
- **PostgreSQL**:
  ```env
  DATABASE_URL=postgresql://postgres:your_password@localhost:5432/smc_tree_census
  # (If your local PostgreSQL runs on port 5433, use localhost:5433)
  ```

*(Optional: Add your `OPENROUTER_API_KEY` or `GEMINI_API_KEY` in `.env` for instant AI tree photo identification).*

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
