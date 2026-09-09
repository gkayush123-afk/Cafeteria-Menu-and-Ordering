from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, os, json, datetime

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="/static")
app.secret_key = "cafeteria-super-secret-key-2026"
DB = os.path.join(os.path.dirname(__file__), "database.db")

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init():
    c = db()
    # Create tables if not exist
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS menu_items (
        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        ingredients TEXT,
        price REAL NOT NULL,
        category TEXT NOT NULL,
        image_url TEXT,
        available INTEGER DEFAULT 1,
        is_special INTEGER DEFAULT 0,
        customization_options TEXT
    );

    CREATE TABLE IF NOT EXISTS pickup_slots (
        slot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        slot_time TEXT UNIQUE NOT NULL,
        capacity INTEGER DEFAULT 10,
        booked INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS orders (
        order_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        pickup_slot_id INTEGER NOT NULL,
        status TEXT DEFAULT 'Received',
        total_amount REAL NOT NULL,
        special_instructions TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(user_id),
        FOREIGN KEY(pickup_slot_id) REFERENCES pickup_slots(slot_id)
    );

    CREATE TABLE IF NOT EXISTS order_items (
        order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        customization TEXT,
        spice_level TEXT,
        addons_selected TEXT,
        unit_price REAL NOT NULL,
        addon_price REAL DEFAULT 0,
        subtotal REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
        FOREIGN KEY(item_id) REFERENCES menu_items(item_id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER UNIQUE NOT NULL,
        method TEXT NOT NULL,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'Paid',
        transaction_id TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
    );
    """)

    # Check if columns exist in menu_items (for backward compatibility / migration)
    cursor = c.execute("PRAGMA table_info(menu_items)")
    cols = [r["name"] for r in cursor.fetchall()]
    if "is_special" not in cols:
        c.execute("ALTER TABLE menu_items ADD COLUMN is_special INTEGER DEFAULT 0")
    if "customization_options" not in cols:
        c.execute("ALTER TABLE menu_items ADD COLUMN customization_options TEXT")

    # Check if columns exist in order_items
    cursor_oi = c.execute("PRAGMA table_info(order_items)")
    cols_oi = [r["name"] for r in cursor_oi.fetchall()]
    if "spice_level" not in cols_oi:
        c.execute("ALTER TABLE order_items ADD COLUMN spice_level TEXT")
    if "addons_selected" not in cols_oi:
        c.execute("ALTER TABLE order_items ADD COLUMN addons_selected TEXT")
    if "addon_price" not in cols_oi:
        c.execute("ALTER TABLE order_items ADD COLUMN addon_price REAL DEFAULT 0")
    if "subtotal" not in cols_oi:
        c.execute("ALTER TABLE order_items ADD COLUMN subtotal REAL DEFAULT 0")

    # Check if menu_items needs rich seed data
    item_count = c.execute("SELECT COUNT(*) n FROM menu_items").fetchone()["n"]
    if item_count == 0 or item_count < 6:
        # Reset and seed with rich menu data
        c.execute("DELETE FROM menu_items")
        seed_items = [
            (
                "Crispy Veg Maharaja Burger",
                "Double-layered crispy spiced vegetable patty, fresh lettuce, melted cheddar, pickles & secret house relish.",
                "Sesame bun, spiced veg patty, lettuce, tomato, cheese slice, house sauce",
                95.0,
                "Fast Food",
                "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=700&auto=format&fit=crop&q=80",
                1,
                1,
                json.dumps({
                    "spice_levels": ["Mild", "Medium", "Spicy 🔥"],
                    "addons": [
                        {"name": "Extra Cheddar Cheese", "price": 20},
                        {"name": "Double Patty", "price": 35},
                        {"name": "Pickled Jalapeños", "price": 15}
                    ]
                })
            ),
            (
                "Paneer Tikka Roll",
                "Chargrilled cottage cheese cubes tossed in spicy tandoori masala, mint chutney, and crunchy bell peppers wrapped in a flaky paratha.",
                "Paneer, whole wheat wrap, mint yogurt sauce, onions, bell peppers, chaat masala",
                85.0,
                "Fast Food",
                "https://images.unsplash.com/photo-1626074353765-517a681e40be?w=700&auto=format&fit=crop&q=80",
                1,
                1,
                json.dumps({
                    "spice_levels": ["Mild", "Medium 🌶️", "Fiery Hot 🌶️🌶️"],
                    "addons": [
                        {"name": "Extra Paneer Chunks", "price": 25},
                        {"name": "Cheese Spread", "price": 15},
                        {"name": "Garlic Dip", "price": 12}
                    ]
                })
            ),
            (
                "Cafeteria Special Masala Maggi",
                "Hot, nostalgic cafeteria-style Maggi noodles cooked with sweet corn, capsicum, green peas, and toasted butter masala.",
                "Maggi noodles, sweet corn, green peas, capsicum, butter, aromatic spices",
                50.0,
                "Snacks",
                "https://images.unsplash.com/photo-1612927601601-6638404737ce?w=700&auto=format&fit=crop&q=80",
                1,
                0,
                json.dumps({
                    "spice_levels": ["Normal", "Spicy 🌶️", "Super Spicy 🌶️🌶️"],
                    "addons": [
                        {"name": "Grated Amul Cheese", "price": 20},
                        {"name": "Butter Tadka", "price": 10},
                        {"name": "Boiled Egg (Optional)", "price": 15}
                    ]
                })
            ),
            (
                "Loaded Peri Peri Fries",
                "Golden crispy French fries tossed in authentic African bird's eye chili seasoning with garlic dip.",
                "Russet potatoes, peri-peri dry seasoning, Himalayan salt, herbs",
                60.0,
                "Snacks",
                "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700&auto=format&fit=crop&q=80",
                1,
                0,
                json.dumps({
                    "spice_levels": ["Mild", "Spicy Peri Peri 🌶️", "Ghost Chili 🌶️🌶️"],
                    "addons": [
                        {"name": "Warm Cheese Sauce", "price": 25},
                        {"name": "Chipotle Mayo", "price": 15}
                    ]
                })
            ),
            (
                "Belgian Chocolate Frappé",
                "Rich, velvety dark Belgian chocolate blended with espresso, chilled milk, and topped with chocolate fudge sauce.",
                "Arabica espresso, Belgian cocoa, chilled whole milk, sugar, chocolate drizzle",
                75.0,
                "Beverages",
                "https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=700&auto=format&fit=crop&q=80",
                1,
                1,
                json.dumps({
                    "spice_levels": [],
                    "addons": [
                        {"name": "Whipped Cream", "price": 15},
                        {"name": "Extra Espresso Shot", "price": 20},
                        {"name": "Crushed Hazelnut", "price": 20},
                        {"name": "Switch to Oat Milk", "price": 25}
                    ]
                })
            ),
            (
                "Iced Caramel Macchiato",
                "Freshly pulled espresso layered over chilled vanilla-infused milk and drizzled with buttery golden caramel sauce.",
                "Espresso, whole milk, vanilla bean extract, caramel drizzle, crushed ice",
                65.0,
                "Beverages",
                "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?w=700&auto=format&fit=crop&q=80",
                1,
                0,
                json.dumps({
                    "spice_levels": [],
                    "addons": [
                        {"name": "Vanilla Cold Foam", "price": 20},
                        {"name": "Extra Caramel Drizzle", "price": 10},
                        {"name": "Sugar Free Syrup", "price": 10}
                    ]
                })
            ),
            (
                "Mediterranean Falafel Bowl",
                "Herb falafel discs served over aromatic spiced quinoa, crunchy cucumbers, cherry tomatoes, pickled cabbage, and garlic tahini dressing.",
                "Chickpeas, herbs, quinoa, cucumber, cherry tomato, tahini, lemon olive dressing",
                110.0,
                "Healthy Bowls",
                "https://images.unsplash.com/photo-1540420773420-3366772f4999?w=700&auto=format&fit=crop&q=80",
                1,
                1,
                json.dumps({
                    "spice_levels": ["Mild", "Medium 🌶️"],
                    "addons": [
                        {"name": "Hummus Dip", "price": 25},
                        {"name": "Pita Bread (2 pcs)", "price": 20},
                        {"name": "Grilled Halloumi", "price": 35}
                    ]
                })
            ),
            (
                "Classic Grilled Club Sandwich",
                "Triple-decker toasted jumbo bread stuffed with cucumber, tomato, potato masala, mint chutney, and melted cheese.",
                "Jumbo bread, potato filling, cucumber, tomato, mint coriander chutney, cheese",
                70.0,
                "Snacks",
                "https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=700&auto=format&fit=crop&q=80",
                1,
                0,
                json.dumps({
                    "spice_levels": ["Mild", "Spicy 🌶️"],
                    "addons": [
                        {"name": "Extra Cheese Slice", "price": 15},
                        {"name": "Butter Toasting", "price": 10}
                    ]
                })
            )
        ]
        c.executemany("""
            INSERT INTO menu_items (name, description, ingredients, price, category, image_url, available, is_special, customization_options)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seed_items)

    # Check pickup slots
    slot_count = c.execute("SELECT COUNT(*) n FROM pickup_slots").fetchone()["n"]
    if slot_count == 0:
        default_slots = [
            ("11:30 AM", 15),
            ("12:00 PM", 15),
            ("12:30 PM", 20),
            ("01:00 PM", 25),
            ("01:30 PM", 20),
            ("02:00 PM", 15),
            ("03:30 PM", 10),
            ("04:30 PM", 15),
            ("05:30 PM", 15)
        ]
        c.executemany("INSERT INTO pickup_slots (slot_time, capacity) VALUES (?, ?)", default_slots)

    c.commit()
    c.close()

# ----------------- ROUTES -----------------

@app.route("/")
def home():
    c = db()
    specials = c.execute("SELECT * FROM menu_items WHERE is_special=1 AND available=1 LIMIT 3").fetchall()
    c.close()
    return render_template("index.html", specials=specials)

@app.route("/menu")
def menu():
    c = db()
    category = request.args.get("category", "all")
    search = request.args.get("q", "").strip()

    query = "SELECT * FROM menu_items WHERE 1=1"
    params = []

    if category == "specials":
        query += " AND is_special=1"
    elif category != "all" and category != "":
        query += " AND category=?"
        params.append(category)

    if search:
        query += " AND (name LIKE ? OR ingredients LIKE ? OR description LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard, wildcard])

    query += " ORDER BY is_special DESC, category, name"
    items = c.execute(query, params).fetchall()
    
    # Get distinct categories for filtering
    cats = [r["category"] for r in c.execute("SELECT DISTINCT category FROM menu_items").fetchall()]
    c.close()
    return render_template("menu.html", items=items, categories=cats, selected_category=category, search_query=search)

@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    c = db()
    slots = c.execute("SELECT * FROM pickup_slots WHERE is_active=1 AND booked < capacity ORDER BY slot_id").fetchall()
    
    if request.method == "GET":
        c.close()
        return render_template("checkout.html", slots=slots)

    # Process POST Checkout
    try:
        cart_data = json.loads(request.form.get("cart_data", "[]"))
    except Exception:
        cart_data = []

    if not cart_data:
        c.close()
        flash("Your cart is empty. Please select food items from the menu.")
        return redirect("/menu")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    slot_id = request.form.get("slot_id")
    payment_method = request.form.get("payment_method", "UPI")
    special_instructions = request.form.get("special_instructions", "").strip()

    if not name or not email or not slot_id:
        c.close()
        flash("Please fill in all required fields.")
        return redirect("/checkout")

    # Validate slot
    slot = c.execute("SELECT * FROM pickup_slots WHERE slot_id=? AND booked < capacity AND is_active=1", (slot_id,)).fetchone()
    if not slot:
        c.close()
        flash("The selected pickup time slot is no longer available. Please select another slot.")
        return redirect("/checkout")

    # Get or create user
    u = c.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if u:
        user_id = u["user_id"]
        c.execute("UPDATE users SET name=?, phone=? WHERE user_id=?", (name, phone or u["phone"], user_id))
    else:
        user_id = c.execute("INSERT INTO users(name, email, phone) VALUES(?, ?, ?)", (name, email, phone)).lastrowid

    # Validate items and calculate exact totals with add-ons
    total_amount = 0.0
    validated_order_items = []

    for item in cart_data:
        item_id = item.get("item_id")
        qty = int(item.get("quantity", 1))
        if qty <= 0:
            continue

        db_item = c.execute("SELECT * FROM menu_items WHERE item_id=?", (item_id,)).fetchone()
        if not db_item:
            c.close()
            flash(f"Item #{item_id} was not found.")
            return redirect("/menu")
        if not db_item["available"]:
            c.close()
            flash(f"Sorry, '{db_item['name']}' is currently out of stock.")
            return redirect("/menu")

        base_price = float(db_item["price"])
        addon_price = float(item.get("addon_price", 0.0))
        spice_level = item.get("spice_level", "")
        custom_note = item.get("customization", "")
        addons_list = item.get("addons_selected", [])
        addons_str = ", ".join(addons_list) if isinstance(addons_list, list) else str(addons_list)

        item_subtotal = (base_price + addon_price) * qty
        total_amount += item_subtotal

        validated_order_items.append({
            "item_id": item_id,
            "quantity": qty,
            "customization": custom_note,
            "spice_level": spice_level,
            "addons_selected": addons_str,
            "unit_price": base_price,
            "addon_price": addon_price,
            "subtotal": item_subtotal
        })

    # Create Order
    order_id = c.execute("""
        INSERT INTO orders (user_id, pickup_slot_id, status, total_amount, special_instructions)
        VALUES (?, ?, 'Received', ?, ?)
    """, (user_id, slot_id, round(total_amount, 2), special_instructions)).lastrowid

    # Insert Order Items
    for oi in validated_order_items:
        c.execute("""
            INSERT INTO order_items (order_id, item_id, quantity, customization, spice_level, addons_selected, unit_price, addon_price, subtotal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, oi["item_id"], oi["quantity"], oi["customization"], oi["spice_level"], oi["addons_selected"], oi["unit_price"], oi["addon_price"], oi["subtotal"]))

    # Update slot booked count
    c.execute("UPDATE pickup_slots SET booked = booked + 1 WHERE slot_id = ?", (slot_id,))

    # Create simulated payment record
    txn_id = f"TXN-{datetime.datetime.now().strftime('%y%m%d')}-{order_id:04d}"
    c.execute("""
        INSERT INTO payments (order_id, method, amount, status, transaction_id)
        VALUES (?, ?, ?, 'Paid', ?)
    """, (order_id, payment_method, round(total_amount, 2), txn_id))

    c.commit()
    c.close()

    flash("Order placed successfully! Track your order status below.")
    return redirect(f"/tracking/{order_id}")

@app.route("/tracking/<int:oid>")
def tracking(oid):
    c = db()
    order = c.execute("""
        SELECT o.*, u.name, u.email, u.phone, p.slot_time, py.method, py.status AS payment_status, py.transaction_id, py.created_at AS payment_date
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN pickup_slots p ON o.pickup_slot_id = p.slot_id
        LEFT JOIN payments py ON o.order_id = py.order_id
        WHERE o.order_id = ?
    """, (oid,)).fetchone()

    if not order:
        c.close()
        return render_template("base.html", content="<div class='card'><h2>Order Not Found</h2><p>Could not find order. <a href='/menu'>Browse Menu</a></p></div>"), 404

    items = c.execute("""
        SELECT oi.*, m.name, m.image_url, m.category
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        WHERE oi.order_id = ?
    """, (oid,)).fetchall()
    c.close()

    # Determine status step index
    status_order = ["Received", "Preparing", "Ready for Pickup", "Completed", "Cancelled"]
    current_status = order["status"]
    status_idx = status_order.index(current_status) if current_status in status_order else 0

    return render_template("tracking.html", order=order, items=items, status_idx=status_idx)

@app.route("/receipt/<int:oid>")
def receipt(oid):
    c = db()
    order = c.execute("""
        SELECT o.*, u.name, u.email, u.phone, p.slot_time, py.method, py.status AS payment_status, py.transaction_id, py.created_at AS payment_date
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN pickup_slots p ON o.pickup_slot_id = p.slot_id
        LEFT JOIN payments py ON o.order_id = py.order_id
        WHERE o.order_id = ?
    """, (oid,)).fetchone()

    if not order:
        c.close()
        return "Order not found", 404

    items = c.execute("""
        SELECT oi.*, m.name, m.category
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        WHERE oi.order_id = ?
    """, (oid,)).fetchall()
    c.close()

    subtotal = sum(i["subtotal"] for i in items)
    tax = round(subtotal * 0.05, 2) # 5% GST representation
    grand_total = subtotal + tax

    return render_template("receipt.html", order=order, items=items, subtotal=subtotal, tax=tax, grand_total=grand_total)

@app.route("/history")
def history():
    email = request.args.get("email", "").strip().lower()
    c = db()
    orders_data = []
    if email:
        raw_orders = c.execute("""
            SELECT o.*, p.slot_time, py.method AS payment_method, py.status AS payment_status, py.transaction_id
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            JOIN pickup_slots p ON o.pickup_slot_id = p.slot_id
            LEFT JOIN payments py ON o.order_id = py.order_id
            WHERE LOWER(u.email) = ?
            ORDER BY o.order_id DESC
        """, (email,)).fetchall()

        for o in raw_orders:
            items = c.execute("""
                SELECT oi.*, m.name
                FROM order_items oi
                JOIN menu_items m ON oi.item_id = m.item_id
                WHERE oi.order_id = ?
            """, (o["order_id"],)).fetchall()
            orders_data.append({"order": o, "order_items": items})
    c.close()
    return render_template("history.html", orders=orders_data, email=email)

# ----------------- ADMIN CONTROLLER -----------------

def admin_ok():
    return session.get("admin") is not None

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        if username == "admin" and password == "admin123":
            session["admin"] = "admin"
            flash("Logged in successfully as Administrator.")
            return redirect("/admin")
        else:
            flash("Invalid credentials! Hint: admin / admin123")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Admin logged out.")
    return redirect("/")

@app.route("/admin")
def admin():
    if not admin_ok():
        return redirect("/admin/login")

    c = db()
    # 1. KPI summary
    total_sales = c.execute("SELECT COALESCE(SUM(total_amount), 0) s FROM orders WHERE status != 'Cancelled'").fetchone()["s"]
    total_orders = c.execute("SELECT COUNT(*) n FROM orders").fetchone()["n"]
    active_orders = c.execute("SELECT COUNT(*) n FROM orders WHERE status IN ('Received', 'Preparing', 'Ready for Pickup')").fetchone()["n"]
    avg_order_value = round(total_sales / total_orders, 2) if total_orders > 0 else 0.0

    # 2. Popular Items (Ranked by quantity ordered)
    popular_items = c.execute("""
        SELECT m.name, m.category, m.price, SUM(oi.quantity) AS total_qty, SUM(oi.subtotal) AS total_revenue
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status != 'Cancelled'
        GROUP BY m.item_id
        ORDER BY total_qty DESC
        LIMIT 5
    """).fetchall()

    # 3. Peak Ordering Times (Orders per pickup slot)
    peak_times = c.execute("""
        SELECT p.slot_time, p.capacity, p.booked, COUNT(o.order_id) AS order_count
        FROM pickup_slots p
        LEFT JOIN orders o ON p.slot_id = o.pickup_slot_id
        GROUP BY p.slot_id
        ORDER BY order_count DESC, p.slot_id
    """).fetchall()

    # 4. All Menu items
    items = c.execute("SELECT * FROM menu_items ORDER BY is_special DESC, category, name").fetchall()

    # 5. Orders list (with items summary)
    orders = c.execute("""
        SELECT o.*, u.name, u.email, u.phone, p.slot_time, py.method, py.transaction_id
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN pickup_slots p ON o.pickup_slot_id = p.slot_id
        LEFT JOIN payments py ON o.order_id = py.order_id
        ORDER BY o.order_id DESC
    """).fetchall()

    # Get items for each order
    orders_with_items = []
    for ord_row in orders:
        ord_items = c.execute("""
            SELECT oi.*, m.name
            FROM order_items oi
            JOIN menu_items m ON oi.item_id = m.item_id
            WHERE oi.order_id = ?
        """, (ord_row["order_id"],)).fetchall()
        orders_with_items.append({"order": ord_row, "order_items": ord_items})

    # 6. Pickup Slots
    slots = c.execute("SELECT * FROM pickup_slots ORDER BY slot_id").fetchall()

    c.close()
    return render_template(
        "admin.html",
        total_sales=round(total_sales, 2),
        total_orders=total_orders,
        active_orders=active_orders,
        avg_order_value=avg_order_value,
        popular_items=popular_items,
        peak_times=peak_times,
        items=items,
        orders_data=orders_with_items,
        slots=slots
    )

@app.post("/admin/toggle/<int:i>")
def toggle_stock(i):
    if not admin_ok():
        return redirect("/admin/login")
    c = db()
    c.execute("UPDATE menu_items SET available = 1 - available WHERE item_id = ?", (i,))
    c.commit()
    c.close()
    flash("Item availability updated.")
    return redirect("/admin#menu-section")

@app.post("/admin/special/<int:i>")
def toggle_special(i):
    if not admin_ok():
        return redirect("/admin/login")
    c = db()
    c.execute("UPDATE menu_items SET is_special = 1 - is_special WHERE item_id = ?", (i,))
    c.commit()
    c.close()
    flash("Daily special status updated.")
    return redirect("/admin#menu-section")

@app.post("/admin/status/<int:o>")
def update_status(o):
    if not admin_ok():
        return redirect("/admin/login")
    status = request.form.get("status")
    c = db()
    c.execute("UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE order_id = ?", (status, o))
    c.commit()
    c.close()
    flash(f"Order #{o} status changed to '{status}'.")
    return redirect("/admin#orders-section")

@app.post("/admin/item/add")
def add_item():
    if not admin_ok():
        return redirect("/admin/login")
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "Snacks").strip()
    price = float(request.form.get("price", 0))
    description = request.form.get("description", "").strip()
    ingredients = request.form.get("ingredients", "").strip()
    image_url = request.form.get("image_url", "").strip() or "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=700"
    is_special = 1 if request.form.get("is_special") == "on" else 0
    
    addons_raw = request.form.get("addons_raw", "")
    addons_list = []
    if addons_raw:
        for line in addons_raw.splitlines():
            if ":" in line:
                part_name, part_price = line.split(":", 1)
                try:
                    addons_list.append({"name": part_name.strip(), "price": float(part_price.strip())})
                except ValueError:
                    pass
    
    spice_options = request.form.getlist("spice_options")
    custom_opts = json.dumps({"spice_levels": spice_options, "addons": addons_list})

    c = db()
    c.execute("""
        INSERT INTO menu_items (name, category, price, description, ingredients, image_url, is_special, customization_options)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, category, price, description, ingredients, image_url, is_special, custom_opts))
    c.commit()
    c.close()
    flash(f"Dish '{name}' added to digital menu.")
    return redirect("/admin#menu-section")

@app.post("/admin/item/edit/<int:i>")
def edit_item(i):
    if not admin_ok():
        return redirect("/admin/login")
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    price = float(request.form.get("price", 0))
    description = request.form.get("description", "").strip()
    ingredients = request.form.get("ingredients", "").strip()
    image_url = request.form.get("image_url", "").strip()
    is_special = 1 if request.form.get("is_special") == "on" else 0

    c = db()
    c.execute("""
        UPDATE menu_items
        SET name = ?, category = ?, price = ?, description = ?, ingredients = ?, image_url = ?, is_special = ?
        WHERE item_id = ?
    """, (name, category, price, description, ingredients, image_url, is_special, i))
    c.commit()
    c.close()
    flash(f"Item '{name}' updated successfully.")
    return redirect("/admin#menu-section")

@app.post("/admin/item/delete/<int:i>")
def delete_item(i):
    if not admin_ok():
        return redirect("/admin/login")
    c = db()
    c.execute("DELETE FROM menu_items WHERE item_id = ?", (i,))
    c.commit()
    c.close()
    flash("Menu item deleted.")
    return redirect("/admin#menu-section")

@app.post("/admin/slot/add")
def add_slot():
    if not admin_ok():
        return redirect("/admin/login")
    slot_time = request.form.get("slot_time", "").strip()
    capacity = int(request.form.get("capacity", 15))
    if slot_time:
        c = db()
        try:
            c.execute("INSERT INTO pickup_slots (slot_time, capacity) VALUES (?, ?)", (slot_time, capacity))
            c.commit()
            flash(f"Pickup slot '{slot_time}' added.")
        except sqlite3.IntegrityError:
            flash(f"Slot time '{slot_time}' already exists.")
        c.close()
    return redirect("/admin#slots-section")

@app.post("/admin/slot/reset/<int:s>")
def reset_slot(s):
    if not admin_ok():
        return redirect("/admin/login")
    c = db()
    c.execute("UPDATE pickup_slots SET booked = 0 WHERE slot_id = ?", (s,))
    c.commit()
    c.close()
    flash("Slot capacity counter reset.")
    return redirect("/admin#slots-section")

# ----------------- JSON API -----------------

@app.get("/api/menu")
def api_menu():
    c = db()
    rows = [dict(x) for x in c.execute("SELECT * FROM menu_items ORDER BY category, name")]
    for r in rows:
        if r.get("customization_options"):
            try:
                r["customization_options"] = json.loads(r["customization_options"])
            except Exception:
                pass
    c.close()
    return jsonify(rows)

@app.get("/api/orders/<int:o>")
def api_order(o):
    c = db()
    order = c.execute("""
        SELECT o.*, u.name, u.email, p.slot_time, py.method, py.status AS payment_status, py.transaction_id
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        JOIN pickup_slots p ON o.pickup_slot_id = p.slot_id
        LEFT JOIN payments py ON o.order_id = py.order_id
        WHERE o.order_id = ?
    """, (o,)).fetchone()
    
    if not order:
        c.close()
        return jsonify(error="Order not found"), 404

    items = c.execute("""
        SELECT oi.*, m.name
        FROM order_items oi
        JOIN menu_items m ON oi.item_id = m.item_id
        WHERE oi.order_id = ?
    """, (o,)).fetchall()
    c.close()

    status_stages = ["Received", "Preparing", "Ready for Pickup", "Completed", "Cancelled"]
    current_status = order["status"]
    status_idx = status_stages.index(current_status) if current_status in status_stages else 0

    progress_map = {
        "Received": 25,
        "Preparing": 55,
        "Ready for Pickup": 85,
        "Completed": 100,
        "Cancelled": 0
    }

    return jsonify({
        "order_id": order["order_id"],
        "status": order["status"],
        "status_idx": status_idx,
        "progress_percent": progress_map.get(current_status, 25),
        "slot_time": order["slot_time"],
        "customer_name": order["name"],
        "total_amount": order["total_amount"],
        "payment_status": order["payment_status"],
        "transaction_id": order["transaction_id"],
        "created_at": order["created_at"],
        "items": [dict(it) for it in items]
    })

# Initialize DB on start
init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
