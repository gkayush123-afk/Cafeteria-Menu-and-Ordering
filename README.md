# CaféGo — Cafeteria Ordering Service

## Stack
Frontend: HTML/CSS/JavaScript
Backend: Python Flask
Database: SQLite

## Run
1. Open this folder in VS Code.
2. Terminal:
   `pip install -r requirements.txt`
3. Run:
   `python app.py`
4. Browser:
   `http://127.0.0.1:5000`

## Where is data saved?
The backend automatically creates **database.db** in this project folder.

Data saved there:
- users
- menu_items
- pickup_slots
- orders
- order_items
- payments

Frontend stores only the temporary cart in browser Local Storage. When checkout is submitted, Flask validates the cart and saves permanent data into SQLite.

## Admin
`http://127.0.0.1:5000/admin/login`
Username: `admin`
Password: `admin123`

Admin can change food availability and order status.

## API
GET `/api/menu`
GET `/api/orders/<id>`

The demo payment is simulated; it does not charge real money.
