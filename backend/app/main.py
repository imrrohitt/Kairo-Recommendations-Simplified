from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal, create_db, get_db
from .models import CartItem, Product, User
from .recommender import RecommendationService, ensure_user_exists
from .schemas import CartItemOut, CartUpdateRequest, ProductOut, RecommendationOut, RecommendRequest, RecommendResponse
from .seed import seed_database


settings = get_settings()
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.api_cors_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    create_db()
    with SessionLocal() as db:
        seed_database(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/users")
def list_users(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    users = db.execute(select(User).order_by(User.id)).scalars().all()
    return [{"id": user.id, "name": user.name, "city": user.city} for user in users]


@app.get("/products", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    return db.execute(select(Product).order_by(Product.category, Product.name)).scalars().all()


@app.get("/cart/{user_id}", response_model=list[CartItemOut])
def get_cart(user_id: int, db: Session = Depends(get_db)) -> list[CartItem]:
    user = ensure_user_exists(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return RecommendationService(db).get_cart(user_id)


@app.post("/cart", response_model=list[CartItemOut])
def add_to_cart(payload: CartUpdateRequest, db: Session = Depends(get_db)) -> list[CartItem]:
    if ensure_user_exists(db, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")
    if db.get(Product, payload.product_id) is None:
        raise HTTPException(status_code=404, detail="Product not found")

    cart_item = db.scalar(
        select(CartItem).where(
            CartItem.user_id == payload.user_id,
            CartItem.product_id == payload.product_id,
        )
    )
    if cart_item is None:
        db.add(CartItem(user_id=payload.user_id, product_id=payload.product_id, quantity=payload.quantity))
    else:
        cart_item.quantity = payload.quantity
    db.commit()
    return RecommendationService(db).get_cart(payload.user_id)


@app.delete("/cart/{user_id}/{product_id}", response_model=list[CartItemOut])
def remove_from_cart(user_id: int, product_id: int, db: Session = Depends(get_db)) -> list[CartItem]:
    cart_item = db.scalar(select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
    if cart_item is not None:
        db.delete(cart_item)
        db.commit()
    return RecommendationService(db).get_cart(user_id)


@app.post("/recommend", response_model=RecommendResponse)
def recommend(payload: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    if ensure_user_exists(db, payload.user_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    service = RecommendationService(db)
    cart = service.get_cart(payload.user_id)
    recommendations = service.recommend(payload.user_id, top_k=payload.top_k)
    return RecommendResponse(
        user_id=payload.user_id,
        cart=cart,
        recommendations=[
            RecommendationOut(product=item.product, score=item.score, reason=item.reason)
            for item in recommendations
        ],
    )
