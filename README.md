<p align="center">
  <img src="assets/kairo-logo.svg" alt="Kairo logo" width="620" />
</p>

<h1 align="center">Kairo</h1>

<p align="center">
  <strong>Build recommendation systems, not recommendation pipelines.</strong>
</p>

<p align="center">
  An open-source recommendation development platform for candidate generation,
  feature engineering, ranking, evaluation, deployment, and learning.
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a>
  ·
  <a href="#platform-studios">Studios</a>
  ·
  <a href="#api">API</a>
  ·
  <a href="#roadmap">Roadmap</a>
</p>

<p align="center">
  <img alt="Backend" src="https://img.shields.io/badge/backend-FastAPI-009688" />
  <img alt="Frontend" src="https://img.shields.io/badge/frontend-React-149eca" />
  <img alt="ML" src="https://img.shields.io/badge/ranking-XGBoost-f28c28" />
  <img alt="Database" src="https://img.shields.io/badge/database-SQLAlchemy%20%2B%20SQLite-334155" />
  <img alt="Status" src="https://img.shields.io/badge/status-active%20prototype-0f766e" />
</p>

---

## Overview

Kairo is a recommendation development platform designed for engineers who want to build, understand, and ship recommendation systems without getting buried in infrastructure too early.

It provides a guided workflow for the core recommendation lifecycle:

```text
Connect Data
  -> Create Dataset
  -> Build Features
  -> Train Ranker
  -> Evaluate Quality
  -> Deploy API
  -> Monitor And Learn
```

The current version is intentionally local-first and lightweight. It gives you a working recommender architecture with FastAPI, SQLAlchemy, React, product affinity, feature generation, XGBoost ranking, and versioned platform state. Kafka, Airflow, Spark, Kubernetes, and vector databases can come later, when the recommendation system actually needs them.

## Why Kairo

Most recommendation projects turn into pipeline projects before the recommendation logic is clear. Kairo keeps the focus on the parts that matter first:

- Generate candidates from product affinity and historical interactions.
- Build user, item, cart, context, and affinity features.
- Rank candidates with XGBoost or a deterministic fallback scorer.
- Evaluate ranking quality with recommendation-specific metrics.
- Serve recommendations through a clean API.
- Track datasets, feature sets, experiments, models, and deployments as versions.
- Teach the user what is happening at each step.

Kairo is designed for e-commerce, ATS, job boards, marketplaces, content platforms, learning platforms, SaaS products, and modern AI applications.

## Architecture

```text
Frontend Platform UI
  |
  v
FastAPI Backend
  |
  +--> Dataset Studio
  +--> Feature Studio
  +--> Model Studio
  +--> Evaluation Studio
  +--> Deployment Studio
  |
  v
Recommendation Service
  |
  +--> Candidate Generation
  +--> Feature Builder
  +--> XGBoost Ranker or Fallback Scorer
  |
  v
Top-K Recommendations
```

## Platform Studios

Kairo is organized around guided studios. Each studio is both a product workflow and a learning surface.

| Studio | Purpose |
| --- | --- |
| Dataset Studio | Connect users, items, and interactions. Detect important columns and create training datasets. |
| Feature Studio | Build user, item, session, context, and affinity features with plain-language explanations. |
| Model Studio | Train ranking models using simple strategies such as Fast Training, Balanced, and Best Accuracy. |
| Evaluation Studio | Compare ranking quality using Precision@K, Recall@K, NDCG@K, and MAP. |
| Deployment Studio | Create serving versions and expose recommendations through `POST /recommend`. |
| Learning Center | Explain recommendation concepts directly inside the workflow. |
| Monitoring | Track serving health, feature freshness, model readiness, and future drift signals. |

Every major action creates a new version. Kairo does not overwrite datasets, feature sets, experiments, model versions, or deployments.

```text
Project
├── Dataset Version 1
├── Dataset Version 2
├── Feature Set 1
├── Experiment 1
├── Model Version 1
└── Deployment Version 1
```

## Project Structure

```text
kairo/
├── assets/        Logo and project assets
├── backend/       FastAPI app, SQLAlchemy models, platform state, recommender service
├── training/      Offline XGBoost training workflow
├── ml_models/     Saved model artifacts
├── data/          SQLite database and generated datasets
├── notebooks/     Experiments and analysis
├── scripts/       Utility scripts
└── frontend/      React platform UI
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20.19+ or 22.12+
- npm

### 1. Start The Backend

```bash
cd kairo
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/seed_db.py
uvicorn backend.app.main:app --reload
```

The backend runs at:

```text
http://localhost:8000
```

### 2. Start The Frontend

Open a second terminal:

```bash
cd kairo/frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

## API

### Platform

```http
GET /platform/overview
```

Returns the active project, studio definitions, feature catalog, metric guide, version history, and serving example.

```http
POST /platform/projects/{project_id}/versions/{kind}
```

Creates the next immutable version for a platform resource.

Supported `kind` values:

```text
dataset
feature_set
experiment
model
deployment
```

### Recommendation Serving

```http
POST /recommend
```

Request:

```json
{
  "user_id": 1,
  "top_k": 10
}
```

Response:

```json
{
  "user_id": 1,
  "cart": [
    {
      "id": 1,
      "quantity": 1,
      "product": {
        "id": 1,
        "name": "Milk",
        "category": "Dairy",
        "brand": "Amul",
        "price": 32.0
      }
    }
  ],
  "recommendations": [
    {
      "product": {
        "id": 3,
        "name": "Butter",
        "category": "Dairy",
        "brand": "Amul",
        "price": 58.0
      },
      "score": 0.82,
      "reason": "Frequently bought with Milk, Bread"
    }
  ]
}
```

Example:

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "top_k": 10}'
```

### Catalog And Cart

```http
GET    /health
GET    /users
GET    /products
GET    /cart/{user_id}
POST   /cart
DELETE /cart/{user_id}/{product_id}
```

## Training

Kairo works immediately with a fallback scorer. To train and save an XGBoost model:

```bash
cd kairo
source .venv/bin/activate
python training/train.py
```

Generated artifacts:

```text
ml_models/xgb_classifier.pkl
data/training_dataset.csv
```

Restart the backend after training so the recommendation service loads the saved model.

## Configuration

Kairo uses SQLite by default. Copy `.env.example` to `.env` to customize runtime settings:

```bash
cp .env.example .env
```

Default local configuration:

```text
DATABASE_URL=sqlite:///data/kairo.db
REDIS_URL=
MODEL_PATH=ml_models/xgb_classifier.pkl
API_CORS_ORIGIN=http://localhost:5173
```

Example Postgres and Redis configuration:

```text
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/kairo
REDIS_URL=redis://localhost:6379/0
MODEL_PATH=ml_models/xgb_classifier.pkl
API_CORS_ORIGIN=http://localhost:5173
```

Install the Postgres driver if you switch databases:

```bash
pip install psycopg[binary]
```

## Current Capabilities

- Local project state with versioned datasets, feature sets, experiments, models, and deployments.
- Grocery recommendation demo data.
- Product affinity candidate generation.
- Feature builder for cart, user, product, and affinity signals.
- XGBoost model training script.
- Fallback scorer when no model artifact exists.
- FastAPI recommendation API.
- React platform interface with guided studios and learning content.

## Roadmap

| Phase | Focus |
| --- | --- |
| V1 | Product affinity, feature builder, recommendation API, guided platform shell. |
| V2 | CSV upload, schema detection, dataset creation wizard, richer negative sampling. |
| V3 | Offline evaluation jobs, experiment comparison, model registry improvements. |
| V4 | Pluggable candidate generators, LightGBM/CatBoost support, ranker configuration UI. |
| V5 | Deployment environments, monitoring, drift checks, production serving patterns. |

## Development

Run backend checks:

```bash
python3 -m compileall backend training scripts
python scripts/seed_db.py
```

Build the frontend:

```bash
cd frontend
npm run build
```

## License

Open-source license coming soon.
