from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3, os, json
app=Flask(__name__); app.secret_key="cafeteria-demo"
DB=os.path.join(os.path.dirname(__file__),"database.db")

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON"); return c

def init():
    c=db()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL);
    CREATE TABLE IF NOT EXISTS menu_items(item_id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,description TEXT,ingredients TEXT,price REAL NOT NULL,category TEXT NOT NULL,image_url TEXT,available INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS pickup_slots(slot_id INTEGER PRIMARY KEY AUTOINCREMENT,slot_time TEXT UNIQUE NOT NULL,capacity INTEGER DEFAULT 10,booked INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS orders(order_id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,pickup_slot_id INTEGER NOT NULL,status TEXT DEFAULT 'Received',total_amount REAL NOT NULL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(user_id) REFERENCES users(user_id),FOREIGN KEY(pickup_slot_id) REFERENCES pickup_slots(slot_id));
    CREATE TABLE IF NOT EXISTS order_items(order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER NOT NULL,item_id INTEGER NOT NULL,quantity INTEGER NOT NULL,customization TEXT,unit_price REAL NOT NULL,FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE,FOREIGN KEY(item_id) REFERENCES menu_items(item_id));
    CREATE TABLE IF NOT EXISTS payments(payment_id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER UNIQUE NOT NULL,method TEXT NOT NULL,amount REAL NOT NULL,status TEXT DEFAULT 'Paid',transaction_id TEXT,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE);
    """)
    if c.execute("SELECT COUNT(*) n FROM menu_items").fetchone()["n"]==0:
        c.executemany("INSERT INTO menu_items(name,description,ingredients,price,category,image_url) VALUES(?,?,?,?,?,?)",[
        ("Veg Burger","Crispy vegetable burger","Veg patty, bun, lettuce, tomato",60,"Fast Food","https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=700"),
        ("Masala Maggi","Hot cafeteria-style noodles","Noodles, vegetables, spices",40,"Snacks","https://images.unsplash.com/photo-1625398407796-82650a8c8b0c?w=700"),
        ("Cold Coffee","Chilled creamy coffee","Milk, coffee, sugar, ice",50,"Beverages","https://images.unsplash.com/photo-1461023058943-07fcbe16d735?w=700"),
        ("Paneer Roll","Spiced paneer roll","Paneer, roti, onion, capsicum",70,"Fast Food","https://images.unsplash.com/photo-1626074353765-517a681e40be?w=700"),
        ("French Fries","Crispy potato fries","Potato, salt, seasoning",45,"Snacks","https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=700")])
    if c.execute("SELECT COUNT(*) n FROM pickup_slots").fetchone()["n"]==0:
        c.executemany("INSERT INTO pickup_slots(slot_time,capacity) VALUES(?,?)",[(x,10) for x in ["12:30 PM","1:00 PM","1:30 PM","2:00 PM","4:00 PM","5:00 PM"]])
    c.commit(); c.close()

@app.route("/")
def home(): return render_template("index.html")
@app.route("/menu")
def menu():
    c=db(); rows=c.execute("SELECT * FROM menu_items ORDER BY category,name").fetchall(); c.close()
    return render_template("menu.html",items=rows)
@app.route("/cart")
def cart(): return render_template("cart.html")
@app.route("/checkout",methods=["GET","POST"])
def checkout():
    c=db(); slots=c.execute("SELECT * FROM pickup_slots WHERE booked<capacity").fetchall()
    if request.method=="GET": c.close(); return render_template("checkout.html",slots=slots)
    try: cart=json.loads(request.form.get("cart_data","[]"))
    except ValueError: cart=[]
    if not cart: c.close(); flash("Cart is empty."); return redirect("/menu")
    name,email=request.form["name"],request.form["email"]
    u=c.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone()
    uid=u["user_id"] if u else c.execute("INSERT INTO users(name,email) VALUES(?,?)",(name,email)).lastrowid
    slotid=int(request.form["slot_id"]); slot=c.execute("SELECT * FROM pickup_slots WHERE slot_id=? AND booked<capacity",(slotid,)).fetchone()
    if not slot: c.close(); flash("Pickup slot unavailable."); return redirect("/checkout")
    total=0; valid=[]
    for x in cart:
        it=c.execute("SELECT * FROM menu_items WHERE item_id=?",(x["item_id"],)).fetchone()
        if not it or not it["available"]: c.close(); flash("A selected food item is unavailable."); return redirect("/menu")
        q=int(x["quantity"]); total+=it["price"]*q; valid.append((it,q,x.get("customization","")))
    oid=c.execute("INSERT INTO orders(user_id,pickup_slot_id,total_amount) VALUES(?,?,?)",(uid,slotid,total)).lastrowid
    for it,q,custom in valid:
        c.execute("INSERT INTO order_items(order_id,item_id,quantity,customization,unit_price) VALUES(?,?,?,?,?)",(oid,it["item_id"],q,custom,it["price"]))
    c.execute("UPDATE pickup_slots SET booked=booked+1 WHERE slot_id=?",(slotid,))
    c.execute("INSERT INTO payments(order_id,method,amount,status,transaction_id) VALUES(?,?,?,?,?)",(oid,request.form["payment_method"],total,"Paid",f"DEMO{oid:05d}"))
    c.commit(); c.close(); return redirect(f"/tracking/{oid}")
@app.route("/tracking/<int:oid>")
def tracking(oid):
    c=db(); o=c.execute("""SELECT o.*,u.name,u.email,p.slot_time,py.method,py.status payment_status,py.transaction_id
                           FROM orders o JOIN users u ON o.user_id=u.user_id JOIN pickup_slots p ON o.pickup_slot_id=p.slot_id
                           LEFT JOIN payments py ON o.order_id=py.order_id WHERE o.order_id=?""",(oid,)).fetchone()
    items=c.execute("SELECT oi.*,m.name FROM order_items oi JOIN menu_items m ON oi.item_id=m.item_id WHERE oi.order_id=?",(oid,)).fetchall(); c.close()
    if not o:return "Order not found",404
    return render_template("tracking.html",order=o,items=items)
@app.route("/history")
def history():
    email=request.args.get("email",""); c=db()
    rows=c.execute("SELECT o.*,p.slot_time FROM orders o JOIN users u ON o.user_id=u.user_id JOIN pickup_slots p ON o.pickup_slot_id=p.slot_id WHERE u.email=? ORDER BY o.order_id DESC",(email,)).fetchall() if email else []
    c.close(); return render_template("history.html",orders=rows,email=email)
@app.route("/admin/login",methods=["GET","POST"])
def admin_login():
    if request.method=="POST" and request.form["username"]=="admin" and request.form["password"]=="admin123":
        session["admin"]=1; return redirect("/admin")
    if request.method=="POST": flash("Invalid login.")
    return render_template("admin_login.html")
@app.route("/admin/logout")
def logout(): session.pop("admin",None); return redirect("/")
def admin_ok():
    return session.get("admin")
@app.route("/admin")
def admin():
    if not admin_ok(): return redirect("/admin/login")
    c=db(); items=c.execute("SELECT * FROM menu_items ORDER BY item_id DESC").fetchall()
    orders=c.execute("SELECT o.*,u.name,p.slot_time FROM orders o JOIN users u ON o.user_id=u.user_id JOIN pickup_slots p ON o.pickup_slot_id=p.slot_id ORDER BY o.order_id DESC").fetchall()
    sales=c.execute("SELECT COALESCE(SUM(total_amount),0) x FROM orders").fetchone()["x"]; c.close()
    return render_template("admin.html",items=items,orders=orders,sales=sales)
@app.post("/admin/toggle/<int:i>")
def toggle(i):
    if not admin_ok(): return redirect("/admin/login")
    c=db(); c.execute("UPDATE menu_items SET available=1-available WHERE item_id=?",(i,)); c.commit(); c.close(); return redirect("/admin")
@app.post("/admin/status/<int:o>")
def status(o):
    if not admin_ok(): return redirect("/admin/login")
    s=request.form["status"]; c=db(); c.execute("UPDATE orders SET status=? WHERE order_id=?",(s,o)); c.commit(); c.close(); return redirect("/admin")
@app.get("/api/menu")
def api_menu():
    c=db(); r=[dict(x) for x in c.execute("SELECT * FROM menu_items ORDER BY category,name")]; c.close(); return jsonify(r)
@app.get("/api/orders/<int:o>")
def api_order(o):
    c=db(); r=c.execute("SELECT order_id,status,total_amount,created_at FROM orders WHERE order_id=?",(o,)).fetchone(); c.close()
    return (jsonify(dict(r)),200) if r else (jsonify(error="Order not found"),404)

if __name__=="__main__":
    init(); app.run(host="127.0.0.1",port=5000,debug=True)
