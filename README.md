# 🌠 Boston Asteroid Watch

A Django web app that shows the **Top 5 asteroids** most threatening to Boston, MA using the **NASA NeoWs API**.

---

## 📦 Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the server
```bash
cd asteroid_tracker
python manage.py runserver
```

### 3. Open in browser
```
http://127.0.0.1:8000
```

---

## 🔄 How It Works

- On first load, the app fetches asteroid data from NASA NeoWs for the **next 7 days**.
- Results are **cached** in `asteroid_cache.json` so you don't burn API calls on every page view.
- The cache is **keyed by today's date** — it auto-refreshes when the date changes.
- You can also manually click **"Refresh Data"** to force a fresh pull from NASA.

---

## 🎯 Threat Score Formula

Each asteroid receives a 0–100 threat score based on:

| Factor              | Max Points | Notes                              |
|---------------------|------------|------------------------------------|
| Proximity to Earth  | 50 pts     | Scaled against 10M km max          |
| Estimated diameter  | 30 pts     | Scaled against 1000m max           |
| Hazardous flag      | 20 pts     | NASA's official hazardous marker   |

Top 5 highest-scoring asteroids are displayed on the dashboard.

---

## 📁 Project Structure

```
asteroid_tracker/
├── manage.py
├── requirements.txt
├── asteroid_cache.json          ← auto-created on first fetch
├── asteroid_tracker/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── tracker/
    ├── nasa_api.py              ← NASA API service + scoring logic
    ├── views.py                 ← Django views
    ├── urls.py
    └── templates/tracker/
        └── index.html           ← Full frontend
```

---

## 🔑 API Key

The NASA API key is stored in `asteroid_tracker/settings.py`:
```python
NASA_API_KEY = 'I5WbsB1uTaN0r52t76Djc0CHcvC66J6UP9aufKbh'
```

---

## 🌐 API Endpoints

| Endpoint        | Method | Description                        |
|-----------------|--------|------------------------------------|
| `/`             | GET    | Main dashboard                     |
| `/api/refresh/` | POST   | Force-refresh asteroid data        |
