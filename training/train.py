from pathlib import Path
import sys

import joblib
import pandas as pd
from sqlalchemy import select
from xgboost import XGBClassifier

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.app.database import SessionLocal, create_db  # noqa: E402
from backend.app.models import CartItem, Order, OrderItem, Product  # noqa: E402
from backend.app.recommender import RecommendationService  # noqa: E402
from backend.app.seed import rebuild_product_affinity, seed_database  # noqa: E402


FEATURE_COLUMNS = [
    "cart_size",
    "candidate_price",
    "user_total_orders",
    "user_avg_order_value",
    "cart_candidate_affinity",
    "same_category_count",
]


def build_training_frame() -> pd.DataFrame:
    create_db()
    rows: list[dict[str, float]] = []

    with SessionLocal() as db:
        seed_database(db)
        rebuild_product_affinity(db)

        products = db.execute(select(Product).order_by(Product.id)).scalars().all()
        orders = db.execute(select(Order).order_by(Order.created_at)).scalars().all()

        for order in orders:
            purchased_ids = {item.product_id for item in order.items}
            historical_ids = _previously_purchased_product_ids(db, order.user_id, order.id)
            if not historical_ids:
                continue

            cart_items = [
                CartItem(user_id=order.user_id, product_id=product_id, quantity=1, product=db.get(Product, product_id))
                for product_id in historical_ids[:3]
            ]
            service = RecommendationService(db)

            positive_products = [db.get(Product, product_id) for product_id in purchased_ids]
            negative_products = [product for product in products if product.id not in purchased_ids and product.id not in historical_ids]
            candidates = [product for product in positive_products if product is not None] + negative_products[: len(positive_products) * 3]

            for product in candidates:
                features = service.build_features(order.user_id, cart_items, product)
                features["label"] = 1.0 if product.id in purchased_ids else 0.0
                rows.append(features)

    return pd.DataFrame(rows)


def train() -> Path:
    frame = build_training_frame()
    if frame.empty:
        raise RuntimeError("No training rows were created. Seed data may be missing.")

    model = XGBClassifier(
        n_estimators=80,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="binary:logistic",
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(frame[FEATURE_COLUMNS], frame["label"])

    model_dir = ROOT_DIR / "ml_models"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "xgb_classifier.pkl"
    joblib.dump(model, model_path)

    data_dir = ROOT_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    frame.to_csv(data_dir / "training_dataset.csv", index=False)

    return model_path


def _previously_purchased_product_ids(db, user_id: int, before_order_id: int) -> list[int]:
    rows = (
        db.execute(
            select(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .where(Order.user_id == user_id)
            .where(Order.id < before_order_id)
            .order_by(Order.created_at.desc())
        )
        .scalars()
        .all()
    )
    unique_ids = list(dict.fromkeys(rows))
    return unique_ids


if __name__ == "__main__":
    saved_path = train()
    print(f"Saved model to {saved_path}")
