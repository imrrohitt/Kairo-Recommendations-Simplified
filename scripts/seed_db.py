from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))

from backend.app.database import SessionLocal, create_db  # noqa: E402
from backend.app.seed import rebuild_product_affinity, seed_database  # noqa: E402


def main() -> None:
    create_db()
    with SessionLocal() as db:
        seed_database(db)
        rebuild_product_affinity(db)
    print("Database seeded and product_affinity rebuilt.")


if __name__ == "__main__":
    main()
