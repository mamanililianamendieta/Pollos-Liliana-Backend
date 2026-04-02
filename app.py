import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB_FILE = 'pollos.db'

INITIAL_ITEMS = [
    {"id":1,"name":"Hamburguesa Simple","category":"hamburguesas","price":12.00,"description":"Carne jugosa, lechuga fresca, tomate y nuestras salsas clásicas.","image":"images/hamburguesasimple.png","stock":20},
    {"id":2,"name":"Hamburguesa Doble","category":"hamburguesas","price":17.00,"description":"Doble porción de carne y queso para los verdaderos amantes de las burgers.","image":"images/hamburguesadoble.png","stock":20},
    {"id":13,"name":"Hamburguesa Especial","category":"hamburguesas","price":22.00,"description":"Con tocino crujiente, aros de cebolla y nuestra salsa barbacoa secreta.","image":"images/hamburguesaespecial.png","stock":20},
    {"id":3,"name":"Lomito Simple","category":"lomitos","price":15.00,"description":"Tierno lomito de res a la plancha, con chimichurri, lechuga y tomate.","image":"images/lomitosimple.png","stock":20},
    {"id":4,"name":"Lomito Doble","category":"lomitos","price":20.00,"description":"El doble de sabor con extra lomito y huevo frito.","image":"images/lomitodoble.png","stock":20},
    {"id":15,"name":"Lomito Especial","category":"lomitos","price":25.00,"description":"El rey de la casa: lomito, doble queso, tocino, huevo y pimientos.","image":"images/lomitoespecial.png","stock":20},
    {"id":6,"name":"Pollo Económico","category":"pollos","price":10.00,"description":"Una presa de nuestro delicioso pollo con una porción de papas fritas.","image":"images/polloeco.png","stock":20},
    {"id":5,"name":"Pollo Cuarto","category":"pollos","price":15.00,"description":"Jugoso cuarto de pollo marinado a las brasas, acompañado de papas y ensalada.","image":"images/pollocuarto.png","stock":20},
    {"id":16,"name":"Pollo Especial","category":"pollos","price":20.00,"description":"Un jugoso cuarto de pollo con chorizo, papas fritas especiales y doble ensalada.","image":"images/polloespecial.png","stock":20},
    {"id":7,"name":"Coca-Cola 2L","category":"sodas","price":13.00,"description":"La clásica e inconfundible gaseosa para acompañar tu comida.","image":"images/cocacola.png","stock":20},
    {"id":8,"name":"Fanta 2L","category":"sodas","price":13.00,"description":"Refrescante sabor a naranja que te encantará.","image":"images/fanta.png","stock":20},
    {"id":9,"name":"Sprite 2L","category":"sodas","price":13.00,"description":"El toque cítrico perfecto para tu paladar.","image":"images/sprite.png","stock":20},
    {"id":10,"name":"Limonada","category":"refrescos","price":2.00,"description":"Hecha con limones frescos, ideal para calmar la sed.","image":"images/limonada.png","stock":20},
    {"id":11,"name":"Mocochinchi","category":"refrescos","price":2.00,"description":"Bebida tradicional a base de durazno deshidratado y canela.","image":"images/mocochinchi.png","stock":20},
    {"id":12,"name":"Chicha","category":"refrescos","price":2.00,"description":"Clásico refresco hecho de maíz morado, piña y especias.","image":"images/chicha.png","stock":20}
]

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Products table
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image TEXT,
            stock INTEGER NOT NULL
        )
    ''')
    # Sales history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_date TEXT NOT NULL,
            sale_time TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total REAL NOT NULL
        )
    ''')
    # Reservations table (physical visits, does NOT reduce stock)
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            res_date TEXT NOT NULL,
            res_time TEXT NOT NULL,
            created_at TEXT NOT NULL,
            guest_name TEXT NOT NULL,
            visit_date TEXT NOT NULL,
            visit_time TEXT NOT NULL,
            guests INTEGER NOT NULL,

items_json TEXT NOT NULL,
            notes TEXT
        )
    ''')
    # Seed products if empty
    c.execute('SELECT COUNT(*) FROM products')
    if c.fetchone()[0] == 0:
        for item in INITIAL_ITEMS:
            c.execute('''
                INSERT INTO products (id, name, category, price, description, image, stock)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item['id'], item['name'], item['category'], item['price'], item['description'], item['image'], item['stock']))
    conn.commit()
    conn.close()

init_db()

# ─── AUTH ──────────────────────────────────────────────────────────────────────
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    if data and data.get('username') == 'liliana' and data.get('password') == '74420831':
        return jsonify({"success": True, "message": "Autenticado como administrador", "role": "admin", "token": "admin-token-74420831"}), 200
    return jsonify({"success": False, "message": "Credenciales inválidas"}), 401

def is_admin(req):
    token = req.headers.get('Authorization', '').replace('Bearer ', '')
    return token == 'admin-token-74420831'

# ─── PRODUCTS ──────────────────────────────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/products', methods=['POST'])
def add_product():
    data = request.json
    name = data.get('name')
    category = data.get('category')
    price = data.get('price')
    description = data.get('description')
    image = data.get('image') or 'images/logo.png'
    stock = data.get('stock', 0)
    if not name or not category or price is None:
        return jsonify({"success": False, "message": "Faltan campos obligatorios"}), 400
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO products (name, category, price, description, image, stock) VALUES (?, ?, ?, ?, ?, ?)',
              (name, category, price, description, image, stock))
    conn.commit()
    new_id = c.lastrowid
    conn.close()
    return jsonify({"success": True, "id": new_id, "message": "Producto agregado"}), 201

@app.route('/api/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.json
    conn = get_db_connection()
    c = conn.cursor()
    prod = c.execute('SELECT * FROM products WHERE id = ?', (id,)).fetchone()
    if not prod:
        return jsonify({"success": False, "message": "Producto no encontrado"}), 404
    name = data.get('name', prod['name'])
    category = data.get('category', prod['category'])
    price = data.get('price', prod['price'])
    description = data.get('description', prod['description'])
    stock = data.get('stock', prod['stock'])
    c.execute('UPDATE products SET name=?, category=?, price=?, description=?, stock=? WHERE id=?',
              (name, category, price, description, stock, id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Producto actualizado"})

# ─── BUY (saves sale to history) ──────────────────────────────────────────────
@app.route('/api/buy', methods=['POST'])
def buy_items():
    data = request.json
    cart = data.get('cart', [])
    if not cart:
        return jsonify({"success": False, "message": "El carrito está vacío"}), 400

    conn = get_db_connection()
    c = conn.cursor()

    total = 0.0
    sale_items = []

    for item in cart:
        prod_id = item.get('id')
        qty = item.get('quantity', 0)
        prod = c.execute('SELECT * FROM products WHERE id = ?', (prod_id,)).fetchone()
        if prod and prod['stock'] >= qty:
            c.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, prod_id))
            subtotal = prod['price'] * qty
            total += subtotal
            sale_items.append({
                "id": prod_id,
                "name": prod['name'],
                "quantity": qty,
                "price": prod['price'],
                "subtotal": subtotal
            })
        else:
            conn.rollback()
            conn.close()
            return jsonify({"success": False, "message": f"Stock insuficiente para producto ID {prod_id}"}), 400

    # Save sale to history
    now = datetime.now()
    sale_date = now.strftime('%Y-%m-%d')
    sale_time = now.strftime('%H:%M:%S')
    c.execute('INSERT INTO sales (sale_date, sale_time, items_json, total) VALUES (?, ?, ?, ?)',
              (sale_date, sale_time, json.dumps(sale_items), total))

    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Compra procesada con éxito", "total": total})

@app.route('/api/sales', methods=['GET'])
def get_sales():
    if not is_admin(request):
        return jsonify({"success": False, "message": "No autorizado"}), 401

    date_from = request.args.get('from')   # YYYY-MM-DD
    date_to   = request.args.get('to')     # YYYY-MM-DD

    conn = get_db_connection()
    c = conn.cursor()

    if date_from and date_to:
        rows = c.execute('SELECT * FROM sales WHERE sale_date BETWEEN ? AND ? ORDER BY sale_date DESC, sale_time DESC',
                         (date_from, date_to)).fetchall()
    elif date_from:
        rows = c.execute('SELECT * FROM sales WHERE sale_date = ? ORDER BY sale_time DESC',
                         (date_from,)).fetchall()
    else:
        # Last 3 distinct dates with sales
        dates = c.execute("SELECT DISTINCT sale_date FROM sales ORDER BY sale_date DESC LIMIT 3").fetchall()
        if not dates:
            conn.close()
            return jsonify([])
        date_list = [d['sale_date'] for d in dates]
        placeholders = ','.join(['?' for _ in date_list])
        rows = c.execute(f'SELECT * FROM sales WHERE sale_date IN ({placeholders}) ORDER BY sale_date DESC, sale_time DESC',
                         date_list).fetchall()

    conn.close()
    result = []
    for row in rows:
        r = dict(row)
        r['items'] = json.loads(r['items_json'])
        del r['items_json']
        result.append(r)
    return jsonify(result)


@app.route('/api/sales/dates', methods=['GET'])
def get_sale_dates():
    """Returns the last 3 dates that had sales."""
    if not is_admin(request):
        return jsonify({"success": False, "message": "No autorizado"}), 401
    conn = get_db_connection()
    rows = conn.execute("SELECT DISTINCT sale_date FROM sales ORDER BY sale_date DESC LIMIT 3").fetchall()
    conn.close()
    return jsonify([r['sale_date'] for r in rows])

@app.route('/api/reservation', methods=['POST'])
def create_reservation():
    data = request.json
    guest_name  = data.get('name', '')
    visit_date  = data.get('date', '')
    visit_time  = data.get('time', '')
    guests      = data.get('guests', 1)
    items       = data.get('items', [])   # list of {id, name, quantity, price}
    notes       = data.get('notes', '')

    if not guest_name or not visit_date or not visit_time:
        return jsonify({'success': False, 'message': 'Faltan campos obligatorios'}), 400

    now = datetime.now()
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO reservations (res_date, res_time, created_at, guest_name, visit_date, visit_time, guests, items_json, notes) VALUES (?,?,?,?,?,?,?,?,?)',
        (now.strftime('%Y-%m-%d'), now.strftime('%H:%M:%S'), now.isoformat(),
         guest_name, visit_date, visit_time, guests, json.dumps(items), notes)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Reserva registrada'}), 201


@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    if not is_admin(request):
        return jsonify({'success': False, 'message': 'No autorizado'}), 401

    date_from = request.args.get('from')
    date_to   = request.args.get('to')
    conn = get_db_connection()
    c = conn.cursor()

    if date_from and date_to:
        rows = c.execute('SELECT * FROM reservations WHERE visit_date BETWEEN ? AND ? ORDER BY visit_date DESC, visit_time DESC',
                         (date_from, date_to)).fetchall()
    elif date_from:
        rows = c.execute('SELECT * FROM reservations WHERE visit_date = ? ORDER BY visit_time DESC',
                         (date_from,)).fetchall()
    else:
        dates = c.execute('SELECT DISTINCT visit_date FROM reservations ORDER BY visit_date DESC LIMIT 3').fetchall()
        if not dates:
            conn.close(); return jsonify([])
        date_list    = [d['visit_date'] for d in dates]
        placeholders = ','.join(['?'] * len(date_list))
        rows = c.execute(f'SELECT * FROM reservations WHERE visit_date IN ({placeholders}) ORDER BY visit_date DESC, visit_time DESC',
                         date_list).fetchall()

    conn.close()
    result = []
    for row in rows:
        r = dict(row)
        r['items'] = json.loads(r['items_json'])
        del r['items_json']
        result.append(r)
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
