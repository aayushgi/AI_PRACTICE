
import sqlite3
import os

# Get project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Database location
DB_PATH = os.path.join(BASE_DIR, "data", "products.db")


# Database connection
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Create products table
def create_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            brand TEXT,
            category TEXT,
            color TEXT,
            size TEXT,
            price REAL,
            stock_quantity INTEGER
        )
    """)

    conn.commit()
    conn.close()

    print("Products table created successfully!")


# Insert sample products
def insert_sample_products():

    conn = get_connection()
    cursor = conn.cursor()

    products = [
        ("Running Shoes", "Nike", "Footwear", "Red", "9", 2499, 12),
        ("Cotton Shirt", "Roadster", "Clothing", "Blue", "M", 799, 20),
        ("Sports Shoes", "Adidas", "Footwear", "Black", "8", 1999, 15),
        ("Casual T-Shirt", "Puma", "Clothing", "White", "L", 599, 25),
        ("Denim Jeans", "Levis", "Clothing", "Blue", "32", 1499, 10)
    ]

    cursor.executemany("""
        INSERT INTO products
        (product_name, brand, category, color, size, price, stock_quantity)
        SELECT ?, ?, ?, ?, ?, ?, ?
        WHERE NOT EXISTS (
            SELECT 1 FROM products
            WHERE product_name = ?
            AND brand = ?
        )
    """, [
        (*product, product[0], product[1])
        for product in products
    ])


    conn.commit()
    conn.close()

    print("Products inserted successfully!")


# Search products
def search_products(keyword):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM products
        WHERE product_name LIKE ?
        OR brand LIKE ?
        OR category LIKE ?
    """, (
        f"%{keyword}%",
        f"%{keyword}%",
        f"%{keyword}%"
    ))

    results = cursor.fetchall()

    conn.close()

    return results


# Display all products
def show_products():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")

    results = cursor.fetchall()

    conn.close()

    for product in results:
        print(dict(product))




def filter_products(max_price):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM products
        WHERE price <= ?
        ORDER BY price ASC
    """, (max_price,))

    results = cursor.fetchall()

    conn.close()

    return results


# Main execution
if __name__ == "__main__":

    create_table()
    insert_sample_products()

    print("\nSearching for Nike products:\n")

    products = search_products("Nike")

    for product in products:
        print(dict(product))
