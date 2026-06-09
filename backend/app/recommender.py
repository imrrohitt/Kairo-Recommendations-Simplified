from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .cache import FeatureCache
from .config import get_settings
from .models import CartItem, Order, OrderItem, Product, ProductAffinity, User


@dataclass(frozen=True)
class RankedRecommendation:
    product: Product
    score: float
    reason: str


class RecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.cache = FeatureCache()
        self.settings = get_settings()
        self.model = self._load_model()

    def recommend(self, user_id: int, top_k: int = 10) -> list[RankedRecommendation]:
        cart_items = self.get_cart(user_id)
        candidates = self.generate_candidates(cart_items, limit=500)
        if not candidates:
            candidates = self._popular_products(limit=500)

        rows = [self.build_features(user_id, cart_items, candidate) for candidate in candidates]
        features = pd.DataFrame(rows)
        scores = self.score(features)

        ranked: list[RankedRecommendation] = []
        for candidate, feature_row, score in zip(candidates, rows, scores, strict=False):
            reason = self._reason(cart_items, candidate, feature_row)
            ranked.append(RankedRecommendation(product=candidate, score=round(float(score), 4), reason=reason))

        ranked.sort(key=lambda item: item.score, reverse=True)
        return ranked[:top_k]

    def get_cart(self, user_id: int) -> list[CartItem]:
        return (
            self.db.execute(
                select(CartItem)
                .where(CartItem.user_id == user_id)
                .join(Product)
                .order_by(Product.name)
            )
            .scalars()
            .all()
        )

    def generate_candidates(self, cart_items: list[CartItem], limit: int = 500) -> list[Product]:
        cart_product_ids = {item.product_id for item in cart_items}
        if not cart_product_ids:
            return self._popular_products(limit)

        affinity_rows = (
            self.db.execute(
                select(ProductAffinity.related_product_id, func.sum(ProductAffinity.score).label("score"))
                .where(ProductAffinity.source_product_id.in_(cart_product_ids))
                .where(ProductAffinity.related_product_id.not_in(cart_product_ids))
                .group_by(ProductAffinity.related_product_id)
                .order_by(desc("score"))
                .limit(limit)
            )
            .all()
        )
        ids = [row.related_product_id for row in affinity_rows]
        if not ids:
            return self._popular_products(limit)

        products = self.db.execute(select(Product).where(Product.id.in_(ids))).scalars().all()
        by_id = {product.id: product for product in products}
        return [by_id[product_id] for product_id in ids if product_id in by_id]

    def build_features(self, user_id: int, cart_items: list[CartItem], candidate: Product) -> dict[str, float]:
        user_features = self._user_features(user_id)
        cart_product_ids = [item.product_id for item in cart_items]
        cart_size = sum(item.quantity for item in cart_items)
        affinity_score = self._cart_affinity_score(cart_product_ids, candidate.id)
        same_category_count = self._same_category_count(cart_items, candidate.category)

        return {
            "user_id": float(user_id),
            "candidate_id": float(candidate.id),
            "cart_size": float(cart_size),
            "candidate_price": float(candidate.price),
            "user_total_orders": float(user_features["total_orders"]),
            "user_avg_order_value": float(user_features["avg_order_value"]),
            "cart_candidate_affinity": float(affinity_score),
            "same_category_count": float(same_category_count),
        }

    def score(self, features: pd.DataFrame) -> list[float]:
        model_columns = [
            "cart_size",
            "candidate_price",
            "user_total_orders",
            "user_avg_order_value",
            "cart_candidate_affinity",
            "same_category_count",
        ]
        if self.model is not None:
            probabilities = self.model.predict_proba(features[model_columns])[:, 1]
            return probabilities.tolist()

        max_price = max(float(features["candidate_price"].max()), 1.0)
        scores = (
            features["cart_candidate_affinity"] * 0.55
            + (features["same_category_count"] / features["cart_size"].clip(lower=1)) * 0.15
            + (features["user_total_orders"].clip(upper=20) / 20) * 0.10
            + (1 - (features["candidate_price"] / max_price)) * 0.20
        )
        return scores.clip(lower=0, upper=1).tolist()

    def _load_model(self):
        model_path = Path(self.settings.model_path)
        if not model_path.exists():
            return None

        try:
            import joblib

            return joblib.load(model_path)
        except Exception:
            return None

    def _user_features(self, user_id: int) -> dict[str, float]:
        cache_key = f"user_features:{user_id}"
        cached = self.cache.get_json(cache_key)
        if cached is not None:
            return cached

        rows = (
            self.db.execute(
                select(Order.id, func.coalesce(func.sum(Product.price * OrderItem.quantity), 0))
                .join(OrderItem, OrderItem.order_id == Order.id)
                .join(Product, Product.id == OrderItem.product_id)
                .where(Order.user_id == user_id)
                .group_by(Order.id)
            )
            .all()
        )
        values = [float(row[1]) for row in rows]
        features = {
            "total_orders": float(len(values)),
            "avg_order_value": round(sum(values) / len(values), 2) if values else 0.0,
        }
        self.cache.set_json(cache_key, features)
        return features

    def _cart_affinity_score(self, cart_product_ids: list[int], candidate_id: int) -> float:
        if not cart_product_ids:
            return 0.0
        score = self.db.scalar(
            select(func.coalesce(func.sum(ProductAffinity.score), 0.0))
            .where(ProductAffinity.source_product_id.in_(cart_product_ids))
            .where(ProductAffinity.related_product_id == candidate_id)
        )
        return float(score or 0.0)

    @staticmethod
    def _same_category_count(cart_items: list[CartItem], category: str) -> int:
        return sum(1 for item in cart_items if item.product.category == category)

    def _popular_products(self, limit: int) -> list[Product]:
        rows = (
            self.db.execute(
                select(Product, func.count(OrderItem.id).label("purchase_count"))
                .outerjoin(OrderItem, Product.id == OrderItem.product_id)
                .group_by(Product.id)
                .order_by(desc("purchase_count"), Product.name)
                .limit(limit)
            )
            .all()
        )
        return [row[0] for row in rows]

    @staticmethod
    def _reason(cart_items: list[CartItem], candidate: Product, features: dict[str, float]) -> str:
        cart_names = [item.product.name for item in cart_items]
        if features["cart_candidate_affinity"] > 0 and cart_names:
            return f"Frequently bought with {', '.join(cart_names[:2])}"
        if features["same_category_count"] > 0:
            return f"Matches your {candidate.category} cart items"
        return "Popular product from recent orders"


def ensure_user_exists(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)
