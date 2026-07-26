# EcoDep – Energy-Aware Dependency Recommendation System

EcoDep is an MCA Research Project designed to benchmark, evaluate, and recommend energy-efficient open-source software dependencies for software developers and system architects.

## 🚀 Technology Stack
* **Backend Framework:** Django 4.2 LTS / Django REST Framework
* **Database Engine:** MySQL 8.0+
* **Language:** Python 3.10+
* **Front-End:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js

## 📋 Prerequisites
* Python 3.10+ installed
* MySQL Server 8.0+ running locally
* Git installed

## 🛠️ Quick Installation Guide

1. **Clone Repository:**
   ```bash
   git clone https://github.com/<your-username>/EcoDep-Energy-Aware-System.git
   cd EcoDep-Energy-Aware-System
   ```

2. **Create & Activate Virtual Environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Environment Setup:**
   * Copy `.env.example` to `.env`
   * Update database password and secret key credentials in `.env`

5. **MySQL Database Setup:**
   * Create database `ecodep_db` and user `ecodep_user` in MySQL.

6. **Run Initial Server:**
   ```powershell
   python manage.py runserver
   ```
   Access application at `http://127.0.0.1:8000/`

## 📁 Directory Structure Overview
```
EcoDep/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── .vscode/
│   └── settings.json
└── ecodep_core/
```

## 👥 Contributors
* **Lead Researcher:** MCA Research Student
* **Academic Supervisor:** Department of Computer Applications

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
