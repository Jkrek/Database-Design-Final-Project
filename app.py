
#!/usr/bin/env python3
# Simple CLI for e-commerce backend demo using SQLite
import sqlite3
import os
import textwrap

DB_PATH = os.getenv("DB_PATH", "ecommerce.db")
SCHEMA_FILE = "schema_and_seed.sql"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print(f"Database initialized and seeded at {DB_PATH}")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def input_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("Please enter an integer.")

def list_products(conn):
    rows = conn.execute(
        """
        SELECT id, name, category, price, inventory_qty, is_active
        FROM Product
        WHERE is_active = 1
        ORDER BY name
        """
    ).fetchall()
    print("\n-- Products --")
    for r in rows:
        print(f"[{r['id']}] {r['name']} | {r['category']} | ${r['price']:.2f} | stock={r['inventory_qty']}")
    print()

def search_products(conn):
    term = input("Search term: ").strip()
    rows = conn.execute(
        """
        SELECT id, name, category, price, inventory_qty
        FROM Product
        WHERE is_active = 1 AND (name LIKE ? OR category LIKE ?)
        ORDER BY name
        """
    , (f"%{term}%", f"%{term}%")).fetchall()
    print("\n-- Search Results --")
    for r in rows:
        print(f"[{r['id']}] {r['name']} | {r['category']} | ${r['price']:.2f} | stock={r['inventory_qty']}")
    print()

def add_customer(conn):
    name = input("Customer name: ").strip()
    email = input("Customer email: ").strip()
    try:
        conn.execute("INSERT INTO Customer(name,email) VALUES (?,?)", (name, email))
        conn.commit()
        print("Customer added.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")

def add_credit_card(conn):
    customer_id = input_int("Customer ID: ")
    brand = input("Brand (Visa/Mastercard/Amex): ").strip()
    last4 = input("Last 4 digits: ").strip()
    exp_month = input_int("Exp month (1-12): ")
    exp_year = input_int("Exp year (YYYY): ")
    nickname = input("Nickname (e.g., Alice-Visa): ").strip()
    try:
        conn.execute(
            """
            INSERT INTO CreditCard(customer_id, brand, last4, exp_month, exp_year, nickname)
            VALUES (?,?,?,?,?,?)
            """
        , (customer_id, brand, last4, exp_month, exp_year, nickname))
        conn.commit()
        print("Card added.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")

def add_product(conn):
    name = input("Product name: ").strip()
    category = input("Category: ").strip()
    price = float(input("Price: "))
    qty = input_int("Inventory qty: ")
    conn.execute(
        """
        INSERT INTO Product(name, category, price, inventory_qty, is_active)
        VALUES (?,?,?,?,1)
        """
    , (name, category, price, qty))
    conn.commit()
    print("Product added.")

def create_order(conn):
    customer_id = input_int("Customer ID: ")
    cards = conn.execute("SELECT nickname FROM CreditCard WHERE customer_id = ?", (customer_id,)).fetchall()
    if not cards:
        print("No credit cards on file. Please add one first.")
        return
    print("Available cards: " + ", ".join([c[0] for c in cards]))
    payment_method = input("Choose card nickname: ").strip()

    cur = conn.execute(
        'INSERT INTO "Order"(customer_id, status, payment_method) VALUES (?,?,?)',
        (customer_id, "PENDING", payment_method)
    )
    order_id = cur.lastrowid

    while True:
        list_products(conn)
        pid_str = input("Product ID to add (or blank to finish): ").strip()
        if not pid_str:
            break
        pid = int(pid_str)
        qty = input_int("Quantity: ")
        prod = conn.execute(
            "SELECT price, inventory_qty, name FROM Product WHERE id = ? AND is_active = 1",
            (pid,)
        ).fetchone()
        if not prod:
            print("Invalid product.")
            continue
        if qty > prod[1]:
            print(f"Insufficient stock. Available: {prod[1]}")
            continue
        unit_price = float(prod[0])
        line_total = unit_price * qty
        conn.execute(
            """
            INSERT INTO OrderItem(order_id, product_id, quantity, unit_price, line_total)
            VALUES (?,?,?,?,?)
            """
        , (order_id, pid, qty, unit_price, line_total))
        conn.execute(
            "UPDATE Product SET inventory_qty = inventory_qty - ? WHERE id = ?",
            (qty, pid)
        )
        conn.commit()
        print(f"Added {qty} x {prod[2]}")

    tot = conn.execute(
        "SELECT IFNULL(SUM(line_total),0) AS t FROM OrderItem WHERE order_id = ?",
        (order_id,)
    ).fetchone()[0]
    conn.execute(
        'UPDATE "Order" SET total_amount = ?, status = ? WHERE id = ?',
        (tot, "PAID" if tot > 0 else "CANCELLED", order_id)
    )
    conn.commit()
    print(f"Order #{order_id} total = ${tot:.2f}")

def view_orders(conn):
    rows = conn.execute(
        """
        SELECT o.id, c.email, o.created_at, o.status, o.total_amount
        FROM "Order" o
        JOIN Customer c ON c.id = o.customer_id
        ORDER BY o.created_at DESC, o.id DESC
        """
    ).fetchall()
    print("\n-- Orders --")
    for r in rows:
        print(f"#{r[0]} | {r[1]} | {r[2]} | {r[3]} | ${r[4]:.2f}")
    print()

def run_query_file(conn, path="queries.sql"):
    if not os.path.exists(path):
        print("queries.sql not found")
        return
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    for stmt in sql.split(";"):
        s = stmt.strip()
        if not s:
            continue
        try:
            cur = conn.execute(s)
            rows = cur.fetchall()
            if rows:
                print("\n" + "-" * 50)
                print(s)
                print("-" * 50)
                for row in rows[:50]:
                    print(dict(zip([d[0] for d in cur.description], row)))
        except sqlite3.Error as e:
            print(f"Error running statement:\n{s}\n{e}")

def menu():
    print(textwrap.dedent("""
    ==== E-Commerce CLI ====
    1) Initialize & seed database
    2) List products
    3) Search products
    4) Add customer
    5) Add credit card
    6) Add product (staff)
    7) Create order
    8) View orders
    9) Run demo queries
    0) Quit
    """))

def main():
    while True:
        menu()
        choice = input("Choose: ").strip()
        if choice == "1":
            init_db()
        elif choice == "2":
            conn = connect(); list_products(conn); conn.close()
        elif choice == "3":
            conn = connect(); search_products(conn); conn.close()
        elif choice == "4":
            conn = connect(); add_customer(conn); conn.close()
        elif choice == "5":
            conn = connect(); add_credit_card(conn); conn.close()
        elif choice == "6":
            conn = connect(); add_product(conn); conn.close()
        elif choice == "7":
            conn = connect(); create_order(conn); conn.close()
        elif choice == "8":
            conn = connect(); view_orders(conn); conn.close()
        elif choice == "9":
            conn = connect(); run_query_file(conn); conn.close()
        elif choice == "0":
            print("Bye!"); break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main()
