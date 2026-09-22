import sqlite3
from datetime import datetime

DB_NAME = "minpay.db"

db = sqlite3.connect(DB_NAME, check_same_thread=False)
db.row_factory = sqlite3.Row


def init_db():
    db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL,
            stock TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT DEFAULT 'Ожидает оплаты',
            created_at TEXT NOT NULL
        )
    """)

    db.commit()


def add_product(category, title, description, price, stock=""):
    cur = db.execute(
        """
        INSERT INTO products
        (category, title, description, price, stock, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            category,
            title,
            description,
            price,
            stock,
            datetime.now().strftime("%d.%m.%Y %H:%M"),
        ),
    )

    db.commit()
    return cur.lastrowid


def get_products(category=None):
    if category:
        cur = db.execute(
            """
            SELECT *
            FROM products
            WHERE category = ? AND active = 1
            ORDER BY id DESC
            """,
            (category,),
        )
    else:
        cur = db.execute(
            """
            SELECT *
            FROM products
            WHERE active = 1
            ORDER BY id DESC
            """
        )

    return cur.fetchall()


def get_product(product_id):
    cur = db.execute(
        "SELECT * FROM products WHERE id = ?",
        (product_id,),
    )
    return cur.fetchone()


def create_order(user_id, product_id, price, payment_method):
    cur = db.execute(
        """
        INSERT INTO orders
        (user_id, product_id, price, payment_method, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            product_id,
            price,
            payment_method,
            "Ожидает оплаты",
            datetime.now().strftime("%d.%m.%Y %H:%M"),
        ),
    )

    db.commit()
    return cur.lastrowid


def get_user_orders(user_id):
    cur = db.execute(
        """
        SELECT
            orders.*,
            products.title
        FROM orders
        JOIN products ON products.id = orders.product_id
        WHERE orders.user_id = ?
        ORDER BY orders.id DESC
        LIMIT 20
        """,
        (user_id,),
    )

    return cur.fetchall()


def get_all_orders():
    cur = db.execute(
        """
        SELECT
            orders.*,
            products.title
        FROM orders
        JOIN products ON products.id = orders.product_id
        ORDER BY orders.id DESC
        LIMIT 100
        """
    )

    return cur.fetchall()


def delete_product(product_id):
    db.execute(
        "UPDATE products SET active = 0 WHERE id = ?",
        (product_id,),
    )
    db.commit()
