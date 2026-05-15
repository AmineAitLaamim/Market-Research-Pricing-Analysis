# 📦 DealMiner

**Real-time Market Intelligence & Price Analysis Platform**

DealMiner is a high-performance, full-stack platform designed to scrape, aggregate, and analyze product data across multiple e-commerce platforms in real-time. By leveraging advanced data mining techniques, it transforms raw listings into actionable market insights.

---

## 🚀 Key Features

### 🔍 Real-time Multi-Platform Scraping
*   **Unified Search**: Query products across **Avito.ma**, **Jumia**, **Marjane**, **AliExpress**, and **Amazon** simultaneously.
*   **Stealth Technology**: Built-in anti-bot measures including User-Agent rotation, human behavior simulation (randomized mouse moves/scrolling), and automated CAPTCHA detection.
*   **Live Progress**: Watch the scraping process in real-time via WebSockets.

### 🧠 Data Mining Pipeline
*   **Dimensionality Reduction (PCA)**: Visualize hundreds of multi-dimensional product listings in a clear 2D topographical market map.
*   **Intelligent Clustering (DBSCAN)**: Automatically group products into market segments (budget, mid-range, luxury) based on density.
*   **Anomaly Detection (Isolation Forest)**: Instantly identify mispriced items or fake listings as outliers.
*   **Association Rules (FP-Growth)**: Discover hidden relationships between product attributes (e.g., "Gaming" keywords associated with specific price brackets).

### 📊 Analytics Dashboard
*   **Best Deal Detection**: Proprietary scoring algorithm to rank the most valuable listings based on price and rating.
*   **Interactive Charts**: Explore price distributions (Histograms), quartiles (Box Plots), and platform-specific price trends.
*   **Price Intelligence**: Search specific products to see historical price changes and set threshold alerts.

---

## 🛠️ Technology Stack

*   **Frontend**: React (Vite), Recharts (for analytics), Lucide React (icons), Axios (API client).
*   **Backend**: Django 5.x, Django REST Framework, Celery (background tasks).
*   **Data Science**: Scikit-Learn, Pandas, NumPy, mlxtend.
*   **Automation**: Playwright (for dynamic scraping), Redis (task queue & caching).
*   **Infrastructure**: PostgreSQL (relational data), Docker & Docker Compose.

---

## 🚦 Getting Started

### Prerequisites
*   **Python**: 3.11+
*   **Node.js**: 20+
*   **Docker** & **Docker Compose**
*   **uv**: Python package manager (recommended)

### Installation

1.  **Clone & Enter**:
    ```bash
    git clone <repository-url>
    cd Market-Research-Pricing-Analysis
    ```

2.  **Environment Setup**:
    ```bash
    cp backend/.env.example backend/.env
    ```

3.  **Run with Docker (Recommended)**:
    ```bash
    make build
    ```
    This spins up the database, redis, backend, celery worker, and frontend.

4.  **Local Development**:
    *   **Backend**:
        ```bash
        cd backend
        uv sync
        uv run python manage.py migrate
        uv run python manage.py runserver
        ```
    *   **Frontend**:
        ```bash
        cd frontend
        npm install
        npm run dev
        ```

---

## 📂 Project Structure

```text
├── backend/            # Django app, Scraping spiders, Mining modules
├── frontend/           # React application & Visualization components
├── docs/               # Detailed technical documentation
├── docker/             # Docker configuration files
├── tests/              # Integrated test suite
└── Makefile            # Shortcut commands (build, logs, tests)
```

## 📚 Deep Dive Documentation

*   [**Mining Pipeline**](./docs/mining-pipeline.md) - How the data analysis engine works.
*   [**Architecture**](./docs/architecture.md) - System design and component interaction.
*   [**Product Intelligence**](./docs/product-intelligence.md) - Price alerts and tracking logic.
*   [**API Reference**](./docs/api-reference.md) - REST and WebSocket endpoints.
*   [**Anti-Bot Research**](./docs/avito-anti-bot.md) - Bypassing scraper protections.

---

## ⚖️ License
Distributed under the MIT License. See `LICENSE` for more information.
