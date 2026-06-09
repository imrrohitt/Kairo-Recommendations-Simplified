<p align="center">
  <img src="assets/kairo-logo.svg" alt="Kairo logo" width="620" />
</p>

<h1 align="center">Kairo</h1>

<p align="center">
  Build recommendation systems, not recommendation pipelines.
</p>

<p align="center">
  An open-source framework for candidate generation, feature engineering, ranking, evaluation, and serving.
  Designed for e-commerce, ATS, marketplaces, content platforms, and modern AI applications.
</p>

---

## What Is Kairo?

Kairo is a practical recommendation framework for learning, prototyping, and shipping the core pieces of modern recommender architecture.

It is evolving into a Recommendation Development Platform: a guided operating system where backend engineers can connect data, create datasets, build features, train ranking models, evaluate quality, deploy APIs, and learn what each step means.

It focuses on the important product and ML loop:

```text
User Context
  -> Candidate Generation
  -> Feature Engineering
  -> Ranking
  -> Evaluation
  -> Serving
```

The first version is intentionally lightweight. It avoids Kafka, Airflow, Spark, Kubernetes, vector databases, and other infrastructure until they are truly needed. The goal is to make recommendation logic clear, runnable, and easy to extend.

## Why Kairo?

Most recommendation projects become infrastructure projects too early. Kairo keeps the system centered on the recommender itself:

- Candidate generation from product affinity and purchase history
- Feature engineering for users, carts, products, and candidate relationships
- Ranking with XGBoost or a deterministic fallback scorer
- Serving through a FastAPI recommendation API
- A React interface for testing recommendations interactively
- Local-first development with SQLite, with optional Postgres and Redis support

## Current Architecture

```text
Client
  |
  v
FastAPI Recommendation API
  |
  v
Candidate Generation
  |
  v
Feature Builder
  |
  v
XGBoost Ranker or Fallback Scorer
  |
  v
Top-K Recommendations
```

## Studios

Kairo is organized into guided studios:

- Dataset Studio: connect users, items, and interactions, then create versioned training datasets.
- Feature Studio: build user, item, session, context, and affinity features with explanations.
- Model Studio: train ranking models using friendly strategies like Fast Training, Balanced, and Best Accuracy.
- Evaluation Studio: compare models with recommendation metrics such as Precision@K, Recall@K, NDCG@K, and MAP.
- Deployment Studio: create serving versions and expose a stable `POST /recommend` API.
- Learning Center: explain recommendation concepts inside the workflow.
- Monitoring: track serving health, model readiness, feature freshness, and future drift checks.

Every project action creates a new version. Kairo does not overwrite datasets, feature sets, experiments, model versions, or deployments.

## Project Structure

```text
kairo/
├── assets/        Logo and project assets
├── backend/       FastAPI app, SQLAlchemy models, recommender service
├── training/      Offline model training
├── ml_models/     Saved model artifacts
├── data/          SQLite DB and generated datasets
├── notebooks/     Experiments and analysis
├── scripts/       Utility scripts
└── frontend/      React demo application
```

## Quick Start

### 1. Start The Backend

```bash
cd kairo
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python scripts/seed_db.py
uvicorn backend.app.main:app --reload
```

The API runs at:

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

The app runs at:

```text
http://localhost:5173
```

## API

### Health

```http
GET /health
```

### Users

```http
GET /users
```

### Products

```http
GET /products
```

### Cart

```http
GET /cart/{user_id}
POST /cart
DELETE /cart/{user_id}/{product_id}
```

### Recommendations

```http
POST /recommend
```

Platform endpoints:

```http
GET  /platform/overview
POST /platform/projects/{project_id}/versions/{kind}
```

Supported version kinds:

```text
dataset
feature_set
experiment
model
deployment
```

Example:

```bash
curl -X POST http://localhost:8000/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "top_k": 10}'
```

Response shape:

```json
{
  "user_id": 1,
  "cart": [],
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

## Train A Ranking Model

Kairo works immediately with a fallback scorer. To train an XGBoost model:

```bash
cd kairo
source .venv/bin/activate
python training/train.py
```

This generates:

```text
ml_models/xgb_classifier.pkl
data/training_dataset.csv
```

Restart the backend after training so the API loads the model.

## Configuration

Kairo uses SQLite by default for local development. Copy `.env.example` to `.env` to override settings:

```bash
cp .env.example .env
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

## Roadmap

- V1: Product affinity and frequently bought together
- V2: User, cart, product, and affinity feature engineering
- V3: XGBoost ranking and offline evaluation
- V4: Pluggable candidate generators and rankers
- V5: Production-ready evaluation, monitoring, and serving patterns

## Use Cases

- E-commerce product recommendations
- ATS candidate-job matching
- Marketplace discovery
- Content feed ranking
- AI application memory and context ranking

## License

Open-source license coming soon.
