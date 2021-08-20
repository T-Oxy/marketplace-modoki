import mysql.connector

conn = mysql.connector.connect(
    host='127.0.0.1',
    port='3306',
    user='s1811406',
    password='RqwV0TvH',
    database='s1811406'
)

cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS index_test;")
cur.execute("CREATE TABLE index_test(id INT PRIMARY KEY, name VARCHAR(64));")
for j in range(100):
    records = [(i, "s{:0>8d}".format(i)) for i in range(10000*j, 10000*(j+1))]
    cur.executemany("INSERT INTO index_test VALUES (%s, %s);", records)
    conn.commit()

cur.close()
conn.close()
