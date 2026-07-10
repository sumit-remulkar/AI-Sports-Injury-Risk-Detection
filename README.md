# 🏃 AI Sports Injury Risk Detection



# 📌 Milestone 1 – Project Initialization & Core Setup

Milestone 1 establishes the technical foundation of the AI Sports Injury Risk Detection platform.

The objective is to design the complete software architecture, database schema, authentication workflow, athlete profile management system, and project structure before implementing AI-based injury prediction.

---

# 🎯 Milestone Objectives

✅ Define Injury Detection Workflow

✅ Design System Architecture

✅ Design Database Schema

✅ Implement Authentication & Role-Based Access

✅ Athlete Profile Management

✅ Prepare Frontend & Backend Environment

✅ Research Sports Biomechanics Datasets

---

# 🏗 System Architecture

```
                 Athlete / Coach

                        │

                 Upload Video

                        │

             Frontend (React + Vite)

                        │

                FastAPI Backend

                        │

       Authentication (Supabase Auth)

                        │

          PostgreSQL (Supabase DB)

                        │

        Future AI Pose Analysis Engine

                        │

     Injury Risk Detection Dashboard
```

---

# 🔐 Authentication & Authorization

Milestone 1 includes a secure authentication system using **Supabase Authentication**.

### Features

- Email & Password Authentication
- Google OAuth Login
- Secure JWT Authentication
- Role-Based Access Control (RBAC)

### User Roles

| Role | Permissions |
|-------|------------|
| Athlete | Manage own profile & future injury reports |
| Coach | View athlete performance & reports |
| Admin | Platform administration |

---

# 👤 Athlete Profile Module

The athlete profile serves as the primary input for future AI analysis.

### Profile Information

- Full Name
- Date of Birth
- Gender
- Height
- Weight
- Dominant Side
- Primary Sport
- Playing Position
- Experience
- Injury History
- Training Frequency
- Performance Goals

---

# 🗄 Database Design

Major database tables implemented during Milestone 1

```
users

profiles

user_roles

auth

future_analysis

future_reports
```

Database Technology

- PostgreSQL
- Supabase
- Row Level Security (RLS)

---

# 📂 Project Structure

```
AI-Sports-Injury-Risk-Detection

│

├── backend/
│   ├── app/
│   ├── models/
│   ├── routes/
│   ├── schemas/
│   ├── database.py
│   └── main.py
│
├── frontend/
│
├── datasets/
│
├── docs/
│
├── models/
│
├── tests/
│
├── assets/
│   └── banner.png
│
├── requirements.txt
└── README.md
```

---

# 📚 Sports Biomechanics Datasets

Research completed during Milestone 1

| Dataset | Purpose |
|----------|----------|
| Human3.6M | Human Pose Estimation |
| MPII Human Pose | Body Keypoint Detection |
| COCO Keypoints | Pose Landmark Detection |
| SportsPose | Sports Motion Analysis |
| FIFA Injury Dataset | Injury Risk Research |

---

# 🛠 Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS

### Backend

- FastAPI
- Python
- SQLAlchemy
- Pydantic
- Uvicorn

### Database

- PostgreSQL
- Supabase

### Development Tools

- Git
- GitHub
- VS Code

---

# 🚀 Future Milestones

### ✅ Milestone 1 (Completed)

- Project Initialization
- Database Design
- Authentication
- Athlete Profile Management
- Architecture Planning

