from typing import Literal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .models import DatasetVersion, Deployment, Experiment, FeatureSet, ModelVersion, Project


VersionKind = Literal["dataset", "feature_set", "experiment", "model", "deployment"]


STUDIO_STEPS = [
    {
        "id": "dataset",
        "name": "Dataset Studio",
        "tagline": "Connect users, items, and interactions.",
        "why": "Models learn from historical interactions. Kairo creates positive and negative examples so ranking models understand both what users chose and what they ignored.",
        "status": "Ready",
    },
    {
        "id": "features",
        "name": "Feature Studio",
        "tagline": "Create user, item, session, context, and affinity features.",
        "why": "Features translate raw behavior into useful signals. They help the model distinguish frequent users, premium items, category matches, and strong cart relationships.",
        "status": "Ready",
    },
    {
        "id": "models",
        "name": "Model Studio",
        "tagline": "Train ranking models without writing ML code.",
        "why": "Recommendation is a ranking problem. Kairo turns strategy choices like Fast, Balanced, and Best Accuracy into model configuration.",
        "status": "Ready",
    },
    {
        "id": "evaluation",
        "name": "Evaluation Studio",
        "tagline": "Compare ranking quality using recommendation metrics.",
        "why": "Accuracy alone is not enough. Metrics like Precision@K, Recall@K, NDCG, and MAP explain how useful the top recommendations are.",
        "status": "Ready",
    },
    {
        "id": "deployment",
        "name": "Deployment Studio",
        "tagline": "Serve recommendations from a stable API endpoint.",
        "why": "A trained model only creates value when applications can call it. Kairo packages the serving path behind POST /recommend.",
        "status": "Ready",
    },
    {
        "id": "learning",
        "name": "Learning Center",
        "tagline": "Every workflow explains what is happening.",
        "why": "Kairo is a product plus a course. Each screen teaches the recommender concept behind the action.",
        "status": "Always On",
    },
    {
        "id": "monitoring",
        "name": "Monitoring",
        "tagline": "Track model, data, and serving health.",
        "why": "Recommendation systems change with user behavior. Monitoring helps detect drift, stale features, and degraded ranking quality.",
        "status": "Planned",
    },
]


FEATURE_CATALOG = [
    {
        "key": "user_total_orders",
        "name": "User Order Count",
        "group": "User Features",
        "meaning": "How many orders the user has placed.",
        "why": "Frequent users behave differently than new users.",
        "enabled": True,
    },
    {
        "key": "user_avg_order_value",
        "name": "Average Order Value",
        "group": "User Features",
        "meaning": "The user's typical basket value.",
        "why": "It helps rank affordable or premium products appropriately.",
        "enabled": True,
    },
    {
        "key": "candidate_price",
        "name": "Candidate Price",
        "group": "Item Features",
        "meaning": "The price of the item being ranked.",
        "why": "Price often influences conversion and substitution behavior.",
        "enabled": True,
    },
    {
        "key": "cart_candidate_affinity",
        "name": "Cart Candidate Affinity",
        "group": "Session Features",
        "meaning": "How often the candidate is bought with current cart items.",
        "why": "It captures frequently-bought-together behavior.",
        "enabled": True,
    },
    {
        "key": "same_category_count",
        "name": "Same Category Count",
        "group": "Context Features",
        "meaning": "How many cart items share the candidate's category.",
        "why": "It helps rank complementary and substitutable products.",
        "enabled": True,
    },
]


METRIC_GUIDE = [
    {
        "name": "Precision@K",
        "value": 0.42,
        "explanation": "Of the top K recommendations, how many were actually useful?",
    },
    {
        "name": "Recall@K",
        "value": 0.68,
        "explanation": "Of all useful items, how many appeared in the top K?",
    },
    {
        "name": "NDCG@K",
        "value": 0.57,
        "explanation": "Are the best items placed near the top of the list?",
    },
    {
        "name": "MAP",
        "value": 0.39,
        "explanation": "How good is the ranking across many users and queries?",
    },
]


def seed_platform(db: Session) -> None:
    existing = db.scalar(select(Project.id).limit(1))
    if existing:
        return

    project = Project(
        id=1,
        name="Kairo Grocery Recommendations",
        domain="E-commerce",
        description="A guided recommendation development project for cart-aware product recommendations.",
    )
    db.add(project)
    db.flush()

    db.add(
        DatasetVersion(
            project_id=project.id,
            version=1,
            name="Grocery interactions v1",
            status="Ready",
            row_count=64,
            positive_examples=21,
            negative_examples=43,
            metadata_json={
                "detected_columns": {
                    "user": "user_id",
                    "item": "product_id",
                    "timestamp": "created_at",
                    "target": "purchased",
                },
                "sources": ["users", "products", "orders", "order_items", "cart_items"],
            },
        )
    )
    db.add(
        FeatureSet(
            project_id=project.id,
            version=1,
            name="Starter ranking features",
            status="Ready",
            feature_count=len(FEATURE_CATALOG),
            metadata_json={"enabled_features": [feature["key"] for feature in FEATURE_CATALOG if feature["enabled"]]},
        )
    )
    experiment = Experiment(
        project_id=project.id,
        version=1,
        name="Balanced XGBoost baseline",
        strategy="Balanced",
        status="Completed",
        metrics_json={metric["name"]: metric["value"] for metric in METRIC_GUIDE},
        config_json={"algorithm": "XGBoost", "max_depth": 3, "n_estimators": 80, "learning_rate": 0.08},
    )
    db.add(experiment)
    db.flush()
    model = ModelVersion(
        project_id=project.id,
        experiment_id=experiment.id,
        version=1,
        name="xgb-classifier-v1",
        algorithm="XGBoost",
        status="Ready",
        artifact_path="ml_models/xgb_classifier.pkl",
    )
    db.add(model)
    db.flush()
    db.add(
        Deployment(
            project_id=project.id,
            model_version_id=model.id,
            version=1,
            name="recommend-api-v1",
            status="Live",
            endpoint="POST /recommend",
        )
    )
    db.commit()


def platform_overview(db: Session) -> dict[str, object]:
    project = db.scalar(select(Project).order_by(Project.id).limit(1))
    if project is None:
        seed_platform(db)
        project = db.scalar(select(Project).order_by(Project.id).limit(1))

    return {
        "project": _project_dict(project),
        "studios": STUDIO_STEPS,
        "features": FEATURE_CATALOG,
        "metrics": METRIC_GUIDE,
        "versions": {
            "datasets": [_dataset_dict(item) for item in _latest(db, DatasetVersion, project.id, 5)],
            "feature_sets": [_feature_set_dict(item) for item in _latest(db, FeatureSet, project.id, 5)],
            "experiments": [_experiment_dict(item) for item in _latest(db, Experiment, project.id, 5)],
            "models": [_model_dict(item) for item in _latest(db, ModelVersion, project.id, 5)],
            "deployments": [_deployment_dict(item) for item in _latest(db, Deployment, project.id, 5)],
        },
        "serving_example": {
            "endpoint": "POST /recommend",
            "request": {"user_id": 101},
            "response": {"items": [11, 22, 33]},
        },
    }


def create_next_version(db: Session, project_id: int, kind: VersionKind) -> dict[str, object]:
    project = db.get(Project, project_id)
    if project is None:
        raise ValueError("Project not found")

    if kind == "dataset":
        next_version = _next_version(db, DatasetVersion, project_id)
        item = DatasetVersion(
            project_id=project_id,
            version=next_version,
            name=f"Dataset v{next_version}",
            status="Draft",
            row_count=0,
            positive_examples=0,
            negative_examples=0,
            metadata_json={"detected_columns": {}, "sources": []},
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"kind": kind, "item": _dataset_dict(item)}

    if kind == "feature_set":
        next_version = _next_version(db, FeatureSet, project_id)
        item = FeatureSet(
            project_id=project_id,
            version=next_version,
            name=f"Feature Set v{next_version}",
            status="Draft",
            feature_count=0,
            metadata_json={"enabled_features": []},
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"kind": kind, "item": _feature_set_dict(item)}

    if kind == "experiment":
        next_version = _next_version(db, Experiment, project_id)
        item = Experiment(
            project_id=project_id,
            version=next_version,
            name=f"Experiment v{next_version}",
            strategy="Balanced",
            status="Queued",
            metrics_json={},
            config_json={"algorithm": "XGBoost"},
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"kind": kind, "item": _experiment_dict(item)}

    if kind == "model":
        next_version = _next_version(db, ModelVersion, project_id)
        item = ModelVersion(
            project_id=project_id,
            version=next_version,
            name=f"model-v{next_version}",
            algorithm="XGBoost",
            status="Candidate",
            artifact_path=f"ml_models/model_v{next_version}.pkl",
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return {"kind": kind, "item": _model_dict(item)}

    next_version = _next_version(db, Deployment, project_id)
    item = Deployment(
        project_id=project_id,
        version=next_version,
        name=f"recommend-api-v{next_version}",
        status="Draft",
        endpoint="POST /recommend",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"kind": kind, "item": _deployment_dict(item)}


def _latest(db: Session, model, project_id: int, limit: int):
    return (
        db.execute(
            select(model)
            .where(model.project_id == project_id)
            .order_by(desc(model.version))
            .limit(limit)
        )
        .scalars()
        .all()
    )


def _next_version(db: Session, model, project_id: int) -> int:
    current = db.scalar(select(func.coalesce(func.max(model.version), 0)).where(model.project_id == project_id))
    return int(current or 0) + 1


def _project_dict(project: Project) -> dict[str, object]:
    return {
        "id": project.id,
        "name": project.name,
        "domain": project.domain,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
    }


def _dataset_dict(item: DatasetVersion) -> dict[str, object]:
    return {
        "id": item.id,
        "version": item.version,
        "name": item.name,
        "status": item.status,
        "row_count": item.row_count,
        "positive_examples": item.positive_examples,
        "negative_examples": item.negative_examples,
        "metadata": item.metadata_json,
    }


def _feature_set_dict(item: FeatureSet) -> dict[str, object]:
    return {
        "id": item.id,
        "version": item.version,
        "name": item.name,
        "status": item.status,
        "feature_count": item.feature_count,
        "metadata": item.metadata_json,
    }


def _experiment_dict(item: Experiment) -> dict[str, object]:
    return {
        "id": item.id,
        "version": item.version,
        "name": item.name,
        "strategy": item.strategy,
        "status": item.status,
        "metrics": item.metrics_json,
        "config": item.config_json,
    }


def _model_dict(item: ModelVersion) -> dict[str, object]:
    return {
        "id": item.id,
        "version": item.version,
        "name": item.name,
        "algorithm": item.algorithm,
        "status": item.status,
        "artifact_path": item.artifact_path,
    }


def _deployment_dict(item: Deployment) -> dict[str, object]:
    return {
        "id": item.id,
        "version": item.version,
        "name": item.name,
        "status": item.status,
        "endpoint": item.endpoint,
    }
