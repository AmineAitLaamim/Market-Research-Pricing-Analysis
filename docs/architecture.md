# Project Architecture

This document provides a comprehensive overview of the Market Research & Pricing Analysis platform's technical architecture, component interactions, and data flow.

---

## High-Level Overview

The system is designed as a distributed, asynchronous platform that combines real-time scraping with machine learning-based data analysis.

```
┌──────────────────────────────────────────────────────────────────┐
│                          Frontend (React)                        │
│   - Vite + React + Vanilla CSS                                   │
│   - Chart.js / D3.js for visualizations                          │
│   - WebSocket client for real-time progress                      │
└────────────────────┬───────────────────▲─────────────────────────┘
                     │ HTTP API          │ WebSockets
┌────────────────────▼───────────────────┴─────────────────────────┐
│                       Backend (Django)                           │
│   - Django REST Framework (API)                                  │
│   - Django Channels (WebSocket handling)                         │
│   - Celery (Task orchestration)                                  │
└──────────┬───────────────────┬─────────────────────────▲─────────┘
           │                   │                         │
┌──────────▼──────────┐ ┌──────▼──────────────┐ ┌────────┴─────────┐
│      PostgreSQL     │ │        Redis        │ │  Celery Workers  │
│  - Product data     │ │  - Task Queue       │ │  - Scrapers      │
│  - Analysis results │ │  - WS Message Bus   │ │  - Mining Engine │
│  - User data        │ │  - Cache            │ │                  │
└─────────────────────┘ └─────────────────────┘ └──────────────────┘
```

---

## Component Breakdown

### 1. Frontend (`/frontend`)
- **Framework:** React with Vite.
- **State Management:** Context API (Auth, Toast).
- **Styling:** Vanilla CSS (Modular).
- **Visualizations:** Chart.js for price trends, custom D3/SVG for cluster analysis (PCA).
- **Communication:** Axios for REST, native WebSockets for task progress.

### 2. Backend (`/backend`)
- **Framework:** Django 5 + Django REST Framework.
- **Apps:**
    - `authentication`: Custom JWT-based user management.
    - `search`: Core logic for scraping tasks, results persistence, and filtering.
    - `export`: Handles exporting data to CSV/Excel.
    - `ws`: WebSocket consumers and utility for pushing updates.
- **Settings:** Environment-based configuration (dev, prod, test).

### 3. Scraping Engine (`/backend/scraper`)
- **Technology:** Playwright (Python) with `playwright-stealth`.
- **Dispatcher:** `dispatcher.py` orchestrates multi-platform scrapes (Avito, Jumia, etc.).
- **Spiders:** Platform-specific logic for parsing HTML and handling infinite scroll or pagination.
- **Resilience:** Implements user-agent rotation and headless browser management.

### 4. Data Mining Pipeline (`/backend/mining`)
- **Technology:** Scikit-learn, Pandas, NumPy.
- **Pipeline steps:**
    1. **Preprocessing:** Cleaning titles, extracting numeric features, handling missing values.
    2. **Normalization:** Converting all prices to MAD (Moroccan Dirham).
    3. **Clustering:** K-Means clustering (available in pipeline).
    4. **Dimensionality Reduction:** PCA (Principal Component Analysis) to project high-dimensional product data into 2D coordinates for the `ClusterScatter` component.
    5. **Anomaly Detection:** Identifying price outliers.

---

## Detailed Data Flow: The Search Pipeline

The most critical workflow in the system is the **Search Pipeline**, which is fully asynchronous.

1. **User Initiation:** User enters a keyword on the `SearchPage`.
2. **Task Creation:** Frontend calls `POST /api/search/`. Backend creates a unique `task_id` and triggers a Celery task.
3. **Scraping Phase:**
    - Celery worker launches Playwright.
    - Scrapes Avito and Jumia in parallel.
    - Normalizes raw HTML into structured JSON objects.
4. **Mining Phase:**
    - Scraped data is passed to `run_mining_pipeline`.
    - Data is cleaned and feature-engineered.
    - PCA is run to calculate visualization coordinates.
    - "Best Deal" scores are calculated.
5. **Persistence:** Results are saved to the PostgreSQL database, linked to the user.
6. **Real-time Updates:** Throughout steps 3-5, the worker sends progress updates (e.g., "Scraping Avito... 50%") to Redis. Django Channels picks these up and pushes them to the frontend WebSocket.
7. **Completion:** Frontend receives a `SUCCESS` status and fetches the final results from the API.

---

## Detailed Data Flow: The Local Database Search

To minimize unnecessary external requests and bypass slow scraping delays, the platform maintains a searchable local database of all historically scraped items.

1. **User Initiation:** User navigates to the `DatabasePage` and types a query.
2. **Debounced Request:** After 400ms of typing inactivity, the frontend queries `GET /api/analytics/products/?q={query}`.
3. **Backend Aggregation:** The Django REST API uses SQL-level aggregations (`values().annotate(Count, Max, Avg)`) to group identical products across multiple past scrapes. It collapses duplicated entries into single distinct products containing metadata like `scrape_count` and `latest_price_mad`.
4. **Result Rendering:** The frontend displays the grouped products in a grid, bypassing the need for live web scraping entirely.

---

## Technical Stack

| Category | Technology |
| :--- | :--- |
| **Language** | Python 3.12+, JavaScript (ES6+) |
| **Web Framework** | Django 5.0 |
| **API** | Django REST Framework |
| **Frontend** | React 18, Vite |
| **Database** | PostgreSQL |
| **Task Queue** | Celery + Redis |
| **Scraping** | Playwright, BeautifulSoup4 |
| **Data Science** | Scikit-learn, Pandas, NumPy |
| **DevOps** | Docker, Docker Compose, Makefile |

---

## Infrastructure & Deployment

- **Containerization:** The app is fully Dockerized with `docker-compose.yml` for development and `docker-compose.prod.yml` for production.
- **Web Server:** Gunicorn (App Server) + Nginx (Reverse Proxy/Static files).
- **Process Management:** Supervisor is used in some deployment environments to manage Celery workers.
