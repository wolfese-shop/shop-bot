import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "vulfis.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL,
            stock TEXT DEFAULT '',
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT DEFAULT 'Ожидает оплаты',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_user(telegram_id, username, first_name):
    conn = get_connection()

    conn.execute("""
        INSERT INTO users (telegram_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (telegram_id, username, first_name))

    conn.commit()
    conn.close()


def add_product(category, name, description, price, stock):
    conn = get_connection()

    cur = conn.execute("""
        INSERT INTO products
        (category, name, description, price, stock)
        VALUES (?, ?, ?, ?, ?)
    """, (category, name, description, price, stock))

    product_id = cur.lastrowid

    conn.commit()
    conn.close()

    return product_id


def get_products(category):
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM products
        WHERE category = ? AND active = 1
        ORDER BY id DESC
    """, (category,)).fetchall()

    conn.close()
    return rows


def get_product(product_id):
    conn = get_connection()

    row = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()
    return row


def create_order(user_id, product_id, payment_method):
    conn = get_connection()

    cur = conn.execute("""
        INSERT INTO orders
        (user_id, product_id, payment_method)
        VALUES (?, ?, ?)
    """, (user_id, product_id, payment_method))

    order_id = cur.lastrowid

    conn.commit()
    conn.close()

    return order_id


def get_user_orders(user_id):
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            orders.*,
            products.name AS product_name,
            products.price AS product_price
        FROM orders
        JOIN products ON products.id = orders.product_id
        WHERE orders.user_id = ?
        ORDER BY orders.id DESC
    """, (user_id,)).fetchall()

    conn.close()
    return rows


def get_all_orders():
    conn = get_connection()

    rows = conn.execute("""
        SELECT
            orders.*,
            products.name AS product_name,
            products.price AS product_price
        FROM orders
        JOIN products ON products.id = orders.product_id
        ORDER BY orders.id DESC
    """).fetchall()

    conn.close()
    return rows


def get_all_products():
    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """).fetchall()

    conn.close()
    return rows


def deactivate_product(product_id):
    conn = get_connection()

    conn.execute("""
        UPDATE products
        SET active = 0
        WHERE id = ?
    """, (product_id,))

    conn.commit()
    conn.close()
