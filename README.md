# 🎓 Smart Attendance AI — Backend

FastAPI backend for the Smart Attendance AI mobile app.  
**Developer:** John Dilip Kumar Vallamreddi

---

## 📁 Project Structure

```
Smart_Attendance/
├── main.py                          # FastAPI app entry point
├── attendance_system.py             # CLI tools
├── capture_faces.py                 # Capture training images
├── recognize_faces.py               # Live webcam test
├── database.py                      # Standalone DB helper
├── attendance.csv                   # Sample attendance data
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables
│
├── routes/
│   ├── auth.py                      # POST /auth/login
│   ├── students.py                  # GET/POST /students
│   ├── faculty.py                   # GET/POST /faculty
│   ├── attendance.py                # POST /attendance/mark
│   ├── recognition.py               # POST /face/recognize
│   ├── camera.py                    # POST /camera/frame
│   ├── analytics.py                 # GET /analytics/weekly
│   ├── dashboard.py                 # GET /dashboard/admin
│   ├── departments.py               # GET /departments
│   └── session.py                   # POST /messages/parent
│
├── services/
│   ├── face_recognition_service.py  # Face recognition engine
│   ├── camera_attendance_service.py # Camera + attendance logic
│   └── email_service.py             # SMTP email alerts
│
├── database/
│   └── supabase_client.py           # Supabase connection
│
├── utils/
│   └── security.py                  # JWT + password hashing
│
└── dataset/                         # Face images per student
    ├── 21CS045/
    │   ├── 1.jpg
    │   └── 2.jpg
    └── encodings.pkl                # Trained face encodings
```

---

## ⚡ Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

> ⚠️ `dlib` and `face-recognition` require CMake. Install first:
> - **Windows**: `pip install cmake` then `pip install dlib`
> - **Ubuntu**: `sudo apt install cmake libboost-all-dev`

### 2. Configure .env
Edit `.env` with your credentials:
```
SUPABASE_URL=https://fosiooudtagavnsgpvhj.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key   ← Get from Supabase Settings
SECRET_KEY=your_secret_key
EMAIL_USERNAME=your@gmail.com
EMAIL_PASSWORD=your_app_password
```

### 3. Add your AI dataset
Copy your existing trained dataset folder into `dataset/`
```
dataset/
  21CS045/  ← student roll number
    1.jpg
    2.jpg
```

### 4. Train the model
```bash
python attendance_system.py train
```

### 5. Start the server
```bash
python main.py
# OR
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Login (Admin/Faculty/Student) |
| GET | `/auth/profile` | Get current user |
| POST | `/auth/change-password` | Change password |
| GET | `/students` | All students |
| GET | `/students/{id}/attendance` | Student attendance |
| GET | `/students/{id}/attendance/subjects` | Subject-wise % |
| POST | `/students` | Create student |
| GET | `/faculty` | All faculty |
| GET | `/faculty/{id}/classes` | Faculty's classes |
| POST | `/faculty` | Create faculty |
| POST | `/attendance/mark` | Mark attendance |
| POST | `/attendance/mark/bulk` | Bulk mark |
| GET | `/attendance/class/{id}` | Class attendance |
| GET | `/attendance/stats` | Overall stats |
| POST | `/face/recognize` | Recognize face |
| POST | `/face/camera/process` | Camera frame → attendance |
| POST | `/face/register` | Register face |
| POST | `/face/train` | Retrain model |
| POST | `/camera/frame` | Process camera frame |
| GET | `/camera/summary/{class_id}` | Today's summary |
| GET | `/analytics/weekly` | Weekly trend |
| GET | `/analytics/monthly` | Monthly trend |
| GET | `/analytics/departments` | Dept comparison |
| GET | `/analytics/performance` | Performance tiers |
| GET | `/dashboard/admin` | Admin stats |
| GET | `/dashboard/faculty/{id}` | Faculty stats |
| GET | `/dashboard/student/{id}` | Student stats |
| POST | `/messages/parent` | Send parent alert |
| GET | `/health` | Server health check |

---

## 🔐 Authentication

All endpoints (except `/auth/login` and `/health`) require a Bearer token:
```
Authorization: Bearer <access_token>
```

Get the token from `POST /auth/login`.

---

## 📱 Connect to Mobile App

In `src/utils/api.ts`, set:
```typescript
const BASE_URL = 'http://YOUR_PC_IP:8000';
// Example: 'http://192.168.1.100:8000'
```

---

## 🤖 CLI Commands

```bash
# Train face recognition model
python attendance_system.py train

# Test recognition on an image
python attendance_system.py test dataset/21CS045/1.jpg

# Show model stats
python attendance_system.py stats

# List students in dataset
python attendance_system.py list

# Capture new face images (webcam)
python capture_faces.py 21CS045 "Arjun Reddy"

# Live recognition test
python recognize_faces.py

# Test database connection
python database.py
```

---

## 📧 Email Setup (Gmail)

1. Enable 2FA on your Gmail account
2. Go to Google Account → Security → App Passwords
3. Create an App Password for "Mail"
4. Use that password in `.env` as `EMAIL_PASSWORD`

---

## 👨‍💻 Developer

**John Dilip Kumar Vallamreddi** — Web Developer  
Smart Attendance AI v1.0.0
