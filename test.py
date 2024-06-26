import psycopg2
import os

connection_url = os.getenv('DB_CONNECTION_URL')
connection = psycopg2.connect(connection_url)

cursor = connection.cursor()

cursor.execute("SELECT * from public.users;")
record = cursor.fetchall()
print(f'Data From cruddur: {record}')