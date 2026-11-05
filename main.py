
import sqlite3
from datetime import datetime
from pathlib import Path

# ==========================================
# FOODIE - RESTAURANT FOOD ORDERING SYSTEM
# ==========================================

DB_NAME = "restaurant.db"
BILLS_FOLDER = Path("bills")
ADMIN_PASSWORD = "admin123"

# Sample restaurant menu
DEFAULT_MENU = [
    ("Veg Burger", 80),
    ("Margherita Pizza", 150),
    ("White Sauce Pasta", 130),
    ("French Fries", 70),
    ("Cold Coffee", 90),
    ("Paneer Sandwich", 110),
    ("Veg Momos", 100),
    ("Chocolate Brownie", 85)
]


# ==========================================
# DATABASE SETUP
# ==========================================

def connect_db():
    return sqlite3.connect(DB_NAME)


def initialize_database():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT,
            order_date TEXT,
            subtotal REAL,
            tax REAL,
            total REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            food_name TEXT,
            quantity INTEGER,
            price REAL,
            item_total REAL,
            FOREIGN KEY(order_id) REFERENCES orders(id)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM menu")

    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO menu (name, price) VALUES (?, ?)",
            DEFAULT_MENU
        )

    conn.commit()
    conn.close()


# ==========================================
# DISPLAY MENU
# ==========================================

def get_menu():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, price FROM menu ORDER BY id")
    items = cursor.fetchall()

    conn.close()
    return items


def display_menu():
    items = get_menu()

    print("\n========== FOOD MENU ==========")
    print(f"{'ID':<5}{'FOOD ITEM':<25}{'PRICE (Rs.)'}")
    print("------------------------------------------")

    for item_id, name, price in items:
        print(f"{item_id:<5}{name:<25}{price:.2f}")

    print("------------------------------------------")


# ==========================================
# BILL GENERATION
# ==========================================

def generate_bill(order):
    BILLS_FOLDER.mkdir(exist_ok=True)

    bill_text = []
    bill_text.append("=" * 42)
    bill_text.append("              FOODIE RESTAURANT")
    bill_text.append("             ORDER RECEIPT")
    bill_text.append("=" * 42)
    bill_text.append(f"Order ID   : {order['id']}")
    bill_text.append(f"Customer   : {order['customer']}")
    bill_text.append(f"Phone      : {order['phone']}")
    bill_text.append(f"Date       : {order['date']}")
    bill_text.append("-" * 42)
    bill_text.append(f"{'Item':<20}{'Qty':>5}{'Amount':>12}")
    bill_text.append("-" * 42)

    for item in order["items"]:
        bill_text.append(
            f"{item['name']:<20}{item['quantity']:>5}"
            f"{item['total']:>12.2f}"
        )

    bill_text.append("-" * 42)
    bill_text.append(f"Subtotal: Rs. {order['subtotal']:.2f}")
    bill_text.append(f"Tax (5% demonstration): Rs. {order['tax']:.2f}")
    bill_text.append(f"TOTAL: Rs. {order['total']:.2f}")
    bill_text.append("=" * 42)
    bill_text.append("        THANK YOU! VISIT AGAIN")
    bill_text.append("=" * 42)

    bill = "\n".join(bill_text)

    filename = BILLS_FOLDER / f"bill_{order['id']}.txt"
    filename.write_text(bill, encoding="utf-8")

    print("\n" + bill)
    print(f"\nBill saved at: {filename}")


# ==========================================
# PLACE CUSTOMER ORDER
# ==========================================

def customer_section():
    cart = {}

    print("\n========== WELCOME TO FOODIE ==========")

    while True:
        display_menu()
        print("\n1. Add food to cart")
        print("2. View cart")
        print("3. Remove food from cart")
        print("4. Checkout")
        print("5. Back to main menu")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            try:
                food_id = int(input("Enter food ID: "))
                quantity = int(input("Enter quantity: "))

                if quantity <= 0:
                    print("Quantity must be greater than zero.")
                    continue

                menu = get_menu()
                selected = next(
                    (item for item in menu if item[0] == food_id),
                    None
                )

                if selected is None:
                    print("Invalid food ID.")
                    continue

                _, name, price = selected

                if food_id in cart:
                    cart[food_id]["quantity"] += quantity
                else:
                    cart[food_id] = {
                        "name": name,
                        "price": price,
                        "quantity": quantity
                    }

                print(f"{name} added to cart successfully!")

            except ValueError:
                print("Please enter valid numbers.")

        elif choice == "2":
            if not cart:
                print("\nYour cart is empty.")
                continue

            print("\n========== YOUR CART ==========")
            subtotal = 0

            for item in cart.values():
                total = item["price"] * item["quantity"]
                subtotal += total

                print(
                    f"{item['name']} x {item['quantity']} "
                    f"= Rs. {total:.2f}"
                )

            print(f"Subtotal: Rs. {subtotal:.2f}")

        elif choice == "3":
            if not cart:
                print("\nYour cart is empty.")
                continue

            try:
                food_id = int(input("Enter food ID to remove: "))

                if food_id in cart:
                    del cart[food_id]
                    print("Item removed from cart.")
                else:
                    print("Item not found in cart.")

            except ValueError:
                print("Please enter a valid food ID.")

        elif choice == "4":
            if not cart:
                print("\nPlease add food before checkout.")
                continue

            customer_name = input("Enter your name: ").strip()
            phone = input("Enter your phone number: ").strip()

            if not customer_name:
                print("Customer name cannot be empty.")
                continue

            items = []
            subtotal = 0

            for item in cart.values():
                item_total = item["price"] * item["quantity"]
                subtotal += item_total

                items.append({
                    "name": item["name"],
                    "quantity": item["quantity"],
                    "price": item["price"],
                    "total": item_total
                })

            tax = subtotal * 0.05
            total = subtotal + tax
            order_date = datetime.now().strftime("%d-%m-%Y %I:%M %p")

            conn = connect_db()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO orders
                (customer_name, phone, order_date, subtotal, tax, total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                customer_name, phone, order_date,
                subtotal, tax, total
            ))

            order_id = cursor.lastrowid

            for item in items:
                cursor.execute("""
                    INSERT INTO order_items
                    (order_id, food_name, quantity, price, item_total)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    order_id,
                    item["name"],
                    item["quantity"],
                    item["price"],
                    item["total"]
                ))

            conn.commit()
            conn.close()

            order = {
                "id": order_id,
                "customer": customer_name,
                "phone": phone,
                "date": order_date,
                "items": items,
                "subtotal": subtotal,
                "tax": tax,
                "total": total
            }

            generate_bill(order)
            cart.clear()

            print("\nYour order has been placed successfully!")

        elif choice == "5":
            break

        else:
            print("Invalid choice. Please try again.")


# ==========================================
# ADMIN LOGIN
# ==========================================

def admin_login():
    print("\n========== ADMIN LOGIN ==========")

    password = input("Enter admin password: ")

    if password == ADMIN_PASSWORD:
        print("\nLogin successful!")
        return True

    print("\nIncorrect password!")
    return False


# ==========================================
# ADMIN MENU MANAGEMENT
# ==========================================

def add_food():
    name = input("Enter food name: ").strip()

    if not name:
        print("Food name cannot be empty.")
        return

    try:
        price = float(input("Enter food price: "))

        if price <= 0:
            print("Price must be greater than zero.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO menu (name, price) VALUES (?, ?)",
            (name, price)
        )

        conn.commit()
        conn.close()

        print("Food item added successfully!")

    except ValueError:
        print("Please enter a valid price.")


def update_food():
    display_menu()

    try:
        food_id = int(input("Enter food ID to update: "))
        menu = get_menu()

        selected = next(
            (item for item in menu if item[0] == food_id),
            None
        )

        if selected is None:
            print("Food item not found.")
            return

        new_name = input("Enter new food name: ").strip()
        new_price = float(input("Enter new price: "))

        if not new_name or new_price <= 0:
            print("Enter a valid name and positive price.")
            return

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE menu
            SET name = ?, price = ?
            WHERE id = ?
        """, (new_name, new_price, food_id))

        conn.commit()
        conn.close()

        print("Food item updated successfully!")

    except ValueError:
        print("Invalid input.")


def delete_food():
    display_menu()

    try:
        food_id = int(input("Enter food ID to delete: "))

        conn = connect_db()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM menu WHERE id = ?", (food_id,))

        if cursor.rowcount > 0:
            print("Food item deleted successfully!")
        else:
            print("Food item not found.")

        conn.commit()
        conn.close()

    except ValueError:
        print("Please enter a valid food ID.")


# ==========================================
# ORDER HISTORY
# ==========================================

def view_order_history():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, customer_name, order_date, total
        FROM orders
        ORDER BY id DESC
    """)

    orders = cursor.fetchall()
    conn.close()

    print("\n========== ORDER HISTORY ==========")

    if not orders:
        print("No orders found.")
        return

    for order in orders:
        print(
            f"Order ID: {order[0]} | "
            f"Customer: {order[1]} | "
            f"Date: {order[2]} | "
            f"Total: Rs. {order[3]:.2f}"
        )


# ==========================================
# SALES REPORT
# ==========================================

def sales_report():
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(total), 0)
        FROM orders
    """)

    result = cursor.fetchone()
    conn.close()

    print("\n========== SALES REPORT ==========")
    print(f"Total Orders: {result[0]}")
    print(f"Total Sales: Rs. {result[1]:.2f}")


# ==========================================
# ADMIN SECTION
# ==========================================

def admin_section():
    if not admin_login():
        return

    while True:
        print("\n========== ADMIN DASHBOARD ==========")
        print("1. View food menu")
        print("2. Add food item")
        print("3. Update food item")
        print("4. Delete food item")
        print("5. View order history")
        print("6. View sales report")
        print("7. Logout")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            display_menu()
        elif choice == "2":
            add_food()
        elif choice == "3":
            update_food()
        elif choice == "4":
            delete_food()
        elif choice == "5":
            view_order_history()
        elif choice == "6":
            sales_report()
        elif choice == "7":
            print("Admin logged out.")
            break
        else:
            print("Invalid choice. Try again.")


# ==========================================
# MAIN PROGRAM
# ==========================================

def main():
    initialize_database()

    while True:
        print("\n")
        print("=" * 42)
        print("       FOODIE - RESTAURANT SYSTEM")
        print("=" * 42)
        print("1. Customer Section")
        print("2. Admin Section")
        print("3. Exit")

        choice = input("\nEnter your choice: ").strip()

        if choice == "1":
            customer_section()

        elif choice == "2":
            admin_section()

        elif choice == "3":
            print("\nThank you for visiting FOODIE!")
            print("Have a great day!")
            break

        else:
            print("Invalid choice. Please enter 1, 2 or 3.")


# Start the application
if __name__ == "__main__":
    main()


