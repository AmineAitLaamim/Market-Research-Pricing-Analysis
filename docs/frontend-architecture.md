# Frontend Architecture

This document details the frontend architecture of the Market Research & Pricing Analysis platform.

---

## Technical Overview

- **Framework:** React 18
- **Build Tool:** Vite
- **Routing:** React Router DOM v6
- **Styling:** Vanilla CSS (App-wide `index.css`)
- **Visualizations:** Chart.js, D3.js, Recharts (for Analytics)
- **API Client:** Axios
- **Real-time:** Native WebSocket API

---

## Directory Structure

```text
frontend/src/
├── api/          # Axios services for backend endpoints
├── components/   # Reusable UI components (Visualizations, Forms, Layout)
│   └── analytics/# Specialized components for the Product Intelligence page
├── context/      # React Context providers (Auth, Toast Notifications)
├── hooks/        # Custom React hooks (e.g., useAlerts)
├── pages/        # Main route view components
├── utils/        # Shared helper functions
├── App.jsx       # Route definitions and provider wrapping
└── main.jsx      # Application entry point
```

---

## Core Systems

### 1. State Management
The application uses **React Context API** for global state:
- **`AuthContext`**: Manages JWT tokens, user profiles, and login/logout persistence via `localStorage`.
- **`ToastContext`**: Provides a global notification system for success, error, and info messages.

### 2. Authentication Flow
- Public routes: `/login`, `/register`.
- Private routes: Wrapped in a `ProtectedRoute` component that checks for an active session.
- Tokens are sent in the `Authorization: Bearer <token>` header via an Axios interceptor (`api/axios.js`).

### 3. Real-time Search Progress
When a search is initiated:
1. The frontend initiates a search via `POST /api/search/`.
2. It receives a `task_id`.
3. It opens a **WebSocket** connection to `ws://backend/ws/search/<task_id>/`.
4. The `ProgressIndicator` component listens for messages and updates the UI (e.g., "Scraping Avito... 40%").
5. Upon completion, the WebSocket sends a `SUCCESS` message, triggering a data fetch.

### 4. Visualizations
The frontend makes heavy use of visualization libraries to display mining results:
- **`ClusterScatter.jsx` (D3.js):** Renders the 2D PCA results, allowing users to see product clusters and outliers.
- **`PriceHistogram.jsx` (Chart.js):** Shows the distribution of prices for the current search.
- **`BoxPlot.jsx` (Chart.js):** Visualizes price quartiles and statistical spread.
- **`Analytics/PriceChart.jsx` (Recharts):** Displays historical price trends for tracked products.

---

## Key Pages

| Page | Description |
| :--- | :--- |
| **SearchPage** | The entry point where users submit new search queries. |
| **ResultsPage** | Displays the real-time progress, data tables, and mining visualizations for a specific search. |
| **AnalyticsPage** | "Product Intelligence" hub for tracking prices over time and receiving "Buy/Wait" recommendations. |
| **HistoryPage** | List of all previous searches conducted by the user. |
| **AlertsPage** | Management interface for price drop notifications and target price thresholds. |

---

## API Services (`src/api/`)

The API layer is modularized by domain:
- `search.js`: Creating searches, fetching results, and handling filters.
- `analytics.js`: Fetching product history, similar products, and setting thresholds.
- `auth.js`: Login, registration, and logout.
- `history.js`: Accessing archived search data.
- `alerts.js`: Managing user alerts and notifications.

---

## Styling Guidelines
The project uses **Vanilla CSS** with a focus on:
- **Responsive Design:** Flexbox and Grid layouts.
- **Theming:** CSS Variables defined in `index.css` for consistent colors and spacing.
- **Modularity:** Components often have sibling CSS files (though currently centralized in `index.css`).
