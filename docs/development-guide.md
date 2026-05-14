# Development Guide

This guide covers everything you need to know to set up, run, and contribute to the Market Research & Pricing Analysis project.

---

## Prerequisites

- **Python 3.12+**
- **Node.js 18+** & **npm**
- **Docker** & **Docker Compose**
- **PostgreSQL** & **Redis** (if running locally without Docker)

---

## Local Setup (Without Docker)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

### 3. Environment Variables
Copy `.env.example` to `.env` in both `backend/` and `frontend/` (if applicable) and fill in your credentials.

---

## Running the Application

The easiest way to run everything is using the **Makefile** in the root directory.

### Using Docker (Recommended)
```bash
# Start all services (Postgres, Redis, Backend, Frontend, Celery)
make docker-up

# Stop all services
make docker-down
```

### Running Components Separately (Manual)

If you prefer running components manually for debugging:

1. **Redis:** Ensure Redis is running on `localhost:6379`.
2. **Celery Worker:**
   ```bash
   cd backend
   celery -A config worker --loglevel=info -P solo
   ```
3. **Django Server:**
   ```bash
   cd backend
   python manage.py runserver
   ```
4. **Frontend Dev Server:**
   ```bash
   cd frontend
   npm run dev
   ```

---

## Project Structure

- `backend/`: Django project.
    - `apps/`: Django applications (auth, search, ws).
    - `config/`: Project settings and URL configurations.
    - `mining/`: Data analysis pipeline and algorithms.
    - `scraper/`: Playwright spiders and scraping logic.
- `frontend/`: React application.
    - `src/api/`: API client services.
    - `src/components/`: Reusable UI components.
    - `src/pages/`: Main view components.
- `docs/`: Technical documentation and anti-bot research.
- `deployment/`: Configuration files for Nginx, Gunicorn, and Supervisor.

---

## Testing

We use **pytest** for both unit and integration tests.

### Run all tests
```bash
make test
```

### Run specific test suites
```bash
# Unit tests
pytest backend/tests/unit

# Integration tests (requires environment setup)
pytest tests/integration
```

---

## Common Makefile Commands

| Command | Description |
| :--- | :--- |
| `make install` | Install all dependencies (Backend + Frontend) |
| `make migrate` | Run Django migrations |
| `make test` | Run the full test suite |
| `make docker-up` | Start the project using Docker Compose |
| `make clean` | Remove temporary files and caches |

---

## Contributing Guidelines

1. **Branching:** Use descriptive branch names (e.g., `feat/add-ebay-spider`, `fix/pca-scaling`).
2. **Linting:** Ensure your code follows PEP 8 for Python and Prettier for JS.
3. **Tests:** Always add tests for new features or bug fixes.
4. **Documentation:** Update the relevant files in `docs/` if you change the architecture or add new modules.
