from datetime import datetime
import secrets
from flask import Flask, render_template, request, session, redirect, url_for
import redis

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)

def create_redis_connection():
    conn = redis.Redis(host='localhost', port=6379, db=1026, charset="utf-8", decode_responses=True)
    return conn

def list_posts(order):  # [1]
    conn = create_redis_connection()
    if order == 'votes':
        post_ids = conn.zrevrange('post:votes', 0, 20)
    else:
        post_ids = conn.zrevrange('post:time', 0, 20)
    print(post_ids)
    posts = [conn.hgetall(post_id) for post_id in post_ids]
    print(posts)
    return posts

@app.route("/")  # [2]
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    sort_method = request.args.get('sort', default='votes', type=str)
    return render_template('index.html', posts=list_posts(sort_method))

@app.route("/login") #[3]
def login():
    return render_template('login.html')

@app.route("/register", methods=["POST"])
def register():
    session['user'] = request.form['user_name']
    return redirect(url_for('index'))

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
    return redirect(url_for('index', sort='time'))

@app.route("/vote", methods=["POST"])
def vote():
    post_id = request.form['post_id']
    conn = create_redis_connection()
    conn.zincrby('post:votes', 1, post_id)
    conn.hincrby(post_id, 'votes', 1)
    return redirect(url_for('index', sort='votes'))


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=11026)
