from flask import Flask, render_template, request
import pymongo

app = Flask(__name__)  # [1]

@app.route("/")  # [2]
def index():
    return render_template('index.html', contents=0)

def create_mongodb_connection():  # [3]
    user = 's1811406'
    pwd = 'RqwV0TvH'
    client = pymongo.MongoClient('mongodb://'+user+':'+pwd+'@dbs1.slis.tsukuba.ac.jp:27018')
    db = client['tweetDB']
    return db

@app.route("/find", methods=["POST"])  # [4]
def find():
    if request.form["value"]:
        db = create_mongodb_connection()
        query = {request.form["field"]: request.form["value"]}
        tweet_data = db.tweets.find(query).limit(100)
        return render_template('index.html', contents=tweet_data)
    else:
        return render_template('index.html', contents=0)

if __name__ == "__main__":  # [5]
    app.run(debug=False, host='0.0.0.0', port=11026)
