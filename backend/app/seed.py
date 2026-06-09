from datetime import datetime, timedelta
from itertools import combinations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import CartItem, Order, OrderItem, Product, ProductAffinity, User


PRODUCTS = [
    ("Milk", "Dairy", "Amul", 32),
    ("Bread", "Bakery", "Britannia", 45),
    ("Butter", "Dairy", "Amul", 58),
    ("Cheese", "Dairy", "Go", 120),
    ("Jam", "Spreads", "Kissan", 85),
    ("Eggs", "Protein", "Farm Fresh", 72),
    ("Banana", "Fruits", "Fresh", 48),
    ("Corn Flakes", "Breakfast", "Kellogg's", 190),
    ("Chips", "Snacks", "Lays", 20),
    ("Cold Coffee", "Beverages", "Nescafe", 60),
    ("Paneer", "Dairy", "Milky Mist", 110),
    ("Tomato", "Vegetables", "Fresh", 35),
    ("Onion", "Vegetables", "Fresh", 40),
    ("Atta", "Staples", "Aashirvaad", 290),
    ("Rice", "Staples", "India Gate", 420),
    ("Dal", "Staples", "Tata Sampann", 160),
    ("Soap", "Personal Care", "Dove", 55),
    ("Shampoo", "Personal Care", "Clinic Plus", 135),
    ("Toothpaste", "Personal Care", "Colgate", 95),
    ("Tea", "Beverages", "Tata Tea", 145),
]


USERS = [
    ("Rohit", "Bengaluru"),
    ("Aisha", "Mumbai"),
    ("Kabir", "Delhi"),
    ("Meera", "Pune"),
]


ORDER_BASKETS = {
    1: [
        ["Milk", "Bread", "Butter"],
        ["Milk", "Corn Flakes", "Banana"],
        ["Bread", "Jam", "Eggs"],
        ["Milk", "Cheese", "Paneer"],
        ["Tea", "Bread", "Butter"],
    ],
    2: [
        ["Rice", "Dal", "Onion", "Tomato"],
        ["Atta", "Paneer", "Tomato"],
        ["Milk", "Tea", "Bread"],
        ["Chips", "Cold Coffee"],
    ],
    3: [
        ["Soap", "Shampoo", "Toothpaste"],
        ["Rice", "Dal", "Atta"],
        ["Milk", "Bread", "Eggs"],
        ["Chips", "Cold Coffee", "Bread"],
    ],
    4: [
        ["Banana", "Milk", "Corn Flakes"],
        ["Bread", "Butter", "Jam"],
        ["Cheese", "Paneer", "Milk"],
        ["Tea", "Bread"],
    ],
}


def seed_database(db: Session) -> None:
    has_users = db.scalar(select(User.id).limit(1))
    if has_users:
        return

    products_by_name: dict[str, Product] = {}
    for idx, (name, category, brand, price) in enumerate(PRODUCTS, start=1):
        product = Product(id=idx, name=name, category=category, brand=brand, price=float(price))
        db.add(product)
        products_by_name[name] = product

    for idx, (name, city) in enumerate(USERS, start=1):
        db.add(User(id=idx, name=name, city=city))

    db.flush()

    order_id = 1
    now = datetime.utcnow()
    for user_id, baskets in ORDER_BASKETS.items():
        for basket_index, basket in enumerate(baskets):
            order = Order(
                id=order_id,
                user_id=user_id,
                created_at=now - timedelta(days=(user_id * 3 + basket_index)),
            )
            db.add(order)
            db.flush()
            for product_name in basket:
                db.add(OrderItem(order_id=order.id, product_id=products_by_name[product_name].id, quantity=1))
            order_id += 1

    db.add(CartItem(user_id=1, product_id=products_by_name["Milk"].id, quantity=1))
    db.add(CartItem(user_id=1, product_id=products_by_name["Bread"].id, quantity=1))
    db.add(CartItem(user_id=2, product_id=products_by_name["Rice"].id, quantity=1))
    db.add(CartItem(user_id=2, product_id=products_by_name["Dal"].id, quantity=1))

    db.commit()
    rebuild_product_affinity(db)


def rebuild_product_affinity(db: Session) -> None:
    db.execute(delete(ProductAffinity))
    orders = db.execute(select(Order)).scalars().all()

    pair_counts: dict[tuple[int, int], int] = {}
    source_counts: dict[int, int] = {}

    for order in orders:
        product_ids = sorted({item.product_id for item in order.items})
        for product_id in product_ids:
            source_counts[product_id] = source_counts.get(product_id, 0) + 1
        for left, right in combinations(product_ids, 2):
            pair_counts[(left, right)] = pair_counts.get((left, right), 0) + 1
            pair_counts[(right, left)] = pair_counts.get((right, left), 0) + 1

    for (source_id, related_id), support in pair_counts.items():
        score = support / max(source_counts.get(source_id, 1), 1)
        db.add(
            ProductAffinity(
                source_product_id=source_id,
                related_product_id=related_id,
                score=round(score, 4),
                support=support,
            )
        )

    db.commit()
