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
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    db = create_mongodb_connection()
    works = db.works.find()
    return render_template('index.html', works=list(works), user_name=session['user'])

@app.route("/login")
def login():
    return render_template('login.html')

@app.route("/find", methods=["POST"])
def find():
    db = create_mongodb_connection()
    if request.form['name'] or request.form['seller']:
        result = db.works.find(filter={'$and': [{'name': {'$regex': request.form['name']}}, {'seller': {'$regex': request.form['seller']}}]}).limit(30)
        return render_template('index.html', works=result, user_name=session['user'])
    else:
        return render_template('index.html', works=db.works.find(), user_name=session['user'])

@app.route("/register", methods=["POST"])
def register():
    user_name = request.form['user_name']
    if user_name:
        session['user'] = user_name
        return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))

@app.route("/sell", methods=["POST"])
def sell():
    db = create_mongodb_connection()
    product = {'name': request.form['name'], 
               'seller': session['user'],
               'detail': request.form['detail'],
               'category': request.form['category'],
               'price': request.form['price']}
    result = db.works.insert_one(product)
    return redirect(url_for('index'))

def get_work(mongo_db, work_id):
    query = {'_id': ObjectId(work_id)}
    return mongo_db.works.find_one(query)

@app.route("/work/<work_id>")
def detail(work_id):
    db = create_mongodb_connection()
    work = get_work(db, work_id)
    return render_template('detail.html', work=work)

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    work_id = request.form['work_id']
    conn.hincrby(cart_key, work_id, 1)
    return redirect(url_for('check_cart'))

@app.route("/remove_from_cart", methods=["POST"])
def remove_from_cart():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    work_id = request.form['work_id']
    conn.hdel(cart_key, work_id)
    return redirect(url_for('check_cart'))

@app.route("/cart")
def check_cart():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    cart_items = conn.hgetall(cart_key)
    db = create_mongodb_connection()
    works = [get_work(db, _id) for _id in cart_items.keys()]
    return render_template('cart.html', works=works, qtys=cart_items)

@app.route("/checkout", methods=["POST"])
def checkout():
    conn = create_redis_connection()
    cart_key = 'cart:' + session['user']
    cart_items = conn.hgetall(cart_key)
    if cart_items:
        db = create_mongodb_connection()
        order = []
        for work_id, qty in cart_items.items():
            order.append({'work_id': work_id, 'qty': qty})
        db.orders.insert_one({'buyer': session['user'], 'items': order})
        conn.delete(cart_key)
        return render_template('thanks.html')
    else:
        return redirect(url_for('index'))

def list_posts(order):
    conn = create_redis_connection()
    if order == 'votes':
        post_ids = conn.zrevrange('post:votes', 0, 20)
    else:
        post_ids = conn.zrevrange('post:time', 0, 20)
    print(post_ids)
    posts = [conn.hgetall(post_id) for post_id in post_ids]
    print(posts)
    return posts

@app.route("/compe")
def compe():
    sort_method = request.args.get('sort', default='votes', type=str)
    return render_template('compe.html', posts=list_posts(sort_method))

@app.route("/post", methods=["POST"])
def post():
    conn = create_redis_connection()
    post_number = str(conn.incr('post:number'))
    post_id = 'post:' + post_number
    now = datetime.now()
    conn.hset(post_id, mapping={
            'id': post_id,
            'user': session['user'],
            'text': request.form['text'], 
            'timestamp': str(now),
            'votes': 0
        })
    conn.zadd('post:votes', {post_id: 0})
    conn.zadd('post:time', {post_id: now.timestamp()})
    return redirect(url_for('compe', sort='time'))

@app.route("/vote", methods=["POST"])
def vote():
    post_id = request.form['post_id']
    conn = create_redis_connection()
    conn.zincrby('post:votes', 1, post_id)
    conn.hincrby(post_id, 'votes', 1)
    return redirect(url_for('compe', sort='votes'))


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=11026)
