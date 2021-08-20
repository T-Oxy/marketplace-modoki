from datetime import datetime
import secrets
from flask import Flask, render_template, request, session, redirect, url_for
from bson.objectid import ObjectId
import redis
import pymongo

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

def create_mongodb_connection():
    user = 's1811406'
    pwd = 'RqwV0TvH'
    client = pymongo.MongoClient('mongodb://'+user+':'+pwd+'@dbs1.slis.tsukuba.ac.jp:27018')
    db = client['s1811406']
    return db

def create_redis_connection():
    conn = redis.Redis(host='localhost', port=6379, db=1026, charset="utf-8", decode_responses=True)
    return conn

@app.route("/")
def index(): #  [1]
    if 'user' not in session:
        return redirect(url_for('login'))
    db = create_mongodb_connection()
    products = db.products.find()
    return render_template('index.html', products=list(products))

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/register", methods=["POST"])
def register():
    user_name = request.form['user_name']
    if user_name:
        session['user'] = user_name
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route("/sell", methods=["POST"])
def sell(): #  [2]
    db = create_mongodb_connection()
    product = {'name': request.form['name'], 
            'seller': session['user']}
    result = db.products.insert_one(product)
    return redirect(url_for('index'))

#  [3]
def get_product(mongo_db, product_id):
    query = {'_id': ObjectId(product_id)}
    return mongo_db.products.find_one(query)

@app.route("/product/<product_id>")
def detail(product_id):
    db = create_mongodb_connection()
    product = get_product(db, product_id)
    return render_template('detail.html', product=product)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    product_id = request.form['product_id']
    conn.hincrby(cart_key, product_id, 1)
    return redirect(url_for('check_cart'))

@app.route("/cart")
def check_cart():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    cart_items = conn.hgetall(cart_key)
    db = create_mongodb_connection()
    products = [get_product(db, _id) for _id in cart_items.keys()]
    return render_template('cart.html', products=products, qtys=cart_items)

@app.route("/checkout", methods=["POST"])
def checkout():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    cart_items = conn.hgetall(cart_key)
    if cart_items:
        db = create_mongodb_connection()
        order = []
        for product_id, qty in cart_items.items():
            order.append({'product_id': product_id, 'qty': qty})
        db.orders.insert_one({'buyer': session['user'], 'items': order})
        conn.delete(cart_key)
        return render_template('thanks.html')
    else:
        return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=11026)
