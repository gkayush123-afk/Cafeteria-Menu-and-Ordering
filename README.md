# CaféGo — Smart Cafeteria Ordering & Pre-Order Service

A full-stack modern campus cafeteria management and pre-ordering platform built with Python Flask, SQLite, and vanilla modern JavaScript & CSS.

## Key Features Implemented

1. **Digital Menu & Custom Orders**
   - Interactive food catalog with HD images, ingredients, categories, and Chef's Daily Specials.
   - Dynamic Customization Modal with Add-ons (e.g. Extra Cheese +₹20, Double Patty +₹35), Spice Levels (Mild, Medium, Spicy), and Special Chef Notes.
   - Real-time client-side live search and category pill filtering.

2. **Pre-Order & Scheduled Pickup**
   - Capacity-managed pickup time slots (e.g. 12:30 PM, 01:00 PM) to eliminate lunch rush queues.
   - Live spot availability counter per time slot with automated capacity locking.

3. **Real-Time Order Tracking & Push Notifications**
   - 4-Stage visual status stepper (`Received` ➔ `Preparing` ➔ `Ready for Pickup` ➔ `Completed`).
   - Seamless background polling engine via `/api/orders/<id>` without page reloads.
   - HTML5 Browser Web Push Notifications & Audio Chime alerts when food is marked *Ready for Pickup*.

4. **Cashless Payments & Tax Receipts**
   - Multi-option simulated payment flows: Dynamic UPI QR Code, Debit/Credit Cards, Mobile Wallets, and Campus Student/Staff ID Credits.
   - Printable & Downloadable Tax Invoices (`/receipt/<id>`) with GST breakdown, itemized add-on tables, transaction IDs, and fast-track counter pickup QR verification.
   - Order history lookup by email.

5. **Admin Dashboard & Kitchen Intelligence Hub**
   - Real-time KPI Stats: Total Revenue (₹), Total Orders, Active In-Kitchen Queue, Average Order Value (AOV).
   - **Top Selling & Popular Dishes Leaderboard** ranked by volume and revenue.
   - **Peak Ordering Times Analytics** with visual capacity load bars per slot.
   - Live Order State Pipeline (`Received` ➔ `Preparing` ➔ `Ready for Pickup` ➔ `Completed` ➔ `Cancelled`).
   - Menu Management CRUD: Add new dishes, edit pricing/ingredients, toggle stock availability, and toggle Daily Specials.
   - Pickup Slot capacity editor and booking counter reset.

---

## Getting Started

### 1. Requirements
- Python 3.8+
- Flask (`pip install -r requirements.txt`)

### 2. Run the Application
```bash
python app.py
```

### 3. Open in Browser
- **User Portal**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Admin Dashboard**: [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)
  - **Username**: `admin`
  - **Password**: `admin123`

---

## API Documentation
- `GET /api/menu`: Returns JSON array of all menu dishes, categories, and customization options.
- `GET /api/orders/<id>`: Returns JSON order state, progress percentage, items, and payment details for real-time live polling.
