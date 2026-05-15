# Market Research & Pricing Analysis

A full-stack platform for real-time product price comparison and data-mining-powered insights.

## Overview
This platform searches products across multiple Moroccan and international e-commerce platforms (Avito, Jumia, Marjane, Amazon, eBay), compares prices in real-time, and delivers insights using advanced data mining techniques.

## Technology Stack
- **Frontend**: React.js (Vite) + Chart.js + D3.js
- **Backend**: Django 5.x + Django REST Framework (DRF)
- **Database**: PostgreSQL 16
- **Task Queue**: Celery + Redis
- **Scraping**: Playwright + Scrapy
- **Real-time**: WebSocket (Django Channels + Daphne)
- **Data Mining**: scikit-learn, mlxtend, Pandas, NumPy
- **Containerization**: Docker + Docker Compose

## Prerequisites
- **Python**: 3.11+
- **Node.js**: 20+
- **Docker** & **Docker Compose**
- **uv**: Python package manager

## Getting Started

### 1. Clone the repository
```bash
git clone <repository-url>
cd Market-Research-Pricing-Analysis
```

### 2. Environment Setup
Copy the example environment file and fill in your values:
```bash
cp backend/.env.example backend/.env
```

### 3. Running with Docker (Recommended)
Use the included `Makefile` to simplify commands. Running `make build` will spin up the following stack:

```text
docker-compose up
├── db             (PostgreSQL database)
├── redis          (Redis cache)
├── backend        (Django app)
├── celery-worker  (Background tasks)
└── frontend       (Vite/Nginx serving React)
```

- **Build and Start**:
  ```bash
  make build
  ```
- **Stop services**:
  ```bash
  make down
  ```
- **View logs**:
  ```bash
  make logs
  ```

### 4. Running Locally (Development)
If you have the dependencies installed:

- **Backend**:
  ```bash
  cd backend
  uv sync
  uv run python manage.py migrate
  uv run python manage.py runserver
  ```
- **Frontend**:
  ```bash
  cd frontend
  npm install
  npm run dev
  ```

## Project Structure
```text
.
├── backend/            # Django application, mining modules, scrapers
├── frontend/           # React.js application
├── docker/             # Docker configuration and compose file
├── tests/              # Centralized test suite
├── Makefile            # Developer shortcuts
└── docker-compose.yml  # Root compose for easy access
```

## 📚 Documentation

For detailed information about the project, please refer to the following guides:

- **[Project Architecture](./docs/architecture.md)**: High-level system design and component overview.
- **[Frontend Architecture](./docs/frontend-architecture.md)**: React components, state management, and visualizations.
- **[API Reference](./docs/api-reference.md)**: REST endpoints and WebSocket protocols.
- **[Development Guide](./docs/development-guide.md)**: Setup instructions, running the app, and testing.
- **[Data Mining Pipeline](./docs/mining-pipeline.md)**: Deep dive into the analysis engine.
- **[Association Rules](./docs/association-rules.md)**: Mining logic, API behavior, thresholds, and frontend controls for association-rule insights.
- **[Product Intelligence](./docs/product-intelligence.md)**: Details on the analytics and price tracking features.
- **[Anti-Bot Research](./docs/avito-anti-bot.md)**: Strategies used to bypass platform protections.

## Features
- **Real-time Scraping**: Dynamic (Playwright) and static (Scrapy) platform crawlers.
- **Multi-Platform Search**: Current first-party platform integrations include `avito`, `jumia`, and `marjane`.
- **Advanced Data Mining**:
  - Price Segmentation (K-Means, DBSCAN)
  - Anomaly Detection (Isolation Forest, LOF)
  - Dimensionality Reduction (PCA for 2D visualization)
  - Association Rule Mining (Apriori, FP-Growth)
- **Live Updates**: Real-time progress tracking via WebSocket.
- **Interactive Dashboard**: Visual price distributions, cluster maps, and deal scoring.
- **Interactive Association Rules**: Users can change the minimum support threshold from the results page and reload rules on demand without rerunning the full scrape.

