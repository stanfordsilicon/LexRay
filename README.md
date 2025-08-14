## LexRay Monorepo

This repository is organized as a monorepo with separate frontend and backend projects.

### Structure

```
LexRay/
├── frontend/                 # Next.js app (Vercel-ready)
│   ├── app/
│   ├── public/
│   ├── package.json
│   └── ...
└── backend/                  # Python CLDR Date Skeleton Converter
    ├── src/
    ├── cldr_data/
    ├── tests/  testing/
    ├── cldr_converter.py
    ├── requirements.txt  setup.py
    └── README.md  QUICKSTART_GUIDE.md
```

### Frontend (Next.js)

- Dev: from `frontend/`

```bash
cd frontend
npm install
npm run dev
```

- Build:

```bash
npm run build && npm start
```

- Deployment: optimized for Vercel. Root should be `frontend/` when configuring.

#### Pages
- `/` Home with links to ingestion flows
- `/single` Single item ingestion (form)
- `/batch` Batch ingestion (CSV upload)

The top-left logo is served from `frontend/public/logo.svg`. Replace this file with your brand asset.

### Backend (Python)

Interactive CLI and batch tools for CLDR date skeleton conversion.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # optional
pip install -r requirements.txt
python cldr_converter.py
```

Tests:

```bash
cd backend
python -m pytest tests/
```

Batch testing data lives in `backend/testing/`.

### API Integration (next steps)

- Expose backend functionality via a small HTTP API (e.g., FastAPI or Flask) inside `backend/`.
- Add API routes in `frontend/` (Next.js route handlers) that call the backend to process single and batch requests.

### Notes

- Node and Python environments are independent.
- When deploying to Vercel, only the `frontend/` directory is required.


