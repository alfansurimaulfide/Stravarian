import sqlite3

conn = sqlite3.connect("user.db")
cursor = conn.cursor()

# cursor.execute("SELECT * FROM user;")
# print(cursor.fetchall())

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())