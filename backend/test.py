# import psycopg2
# import os
# import random
# import string
import uuid

# connection_url = os.getenv('DB_CONNECTION_URL')
# connection = psycopg2.connect(connection_url)

# cursor = connection.cursor()

# cursor.execute("SELECT * from public.users;")
# record = cursor.fetchall()
# print(f'Data From cruddur: {record}')

# string.digits contains the string '0123456789'.
# digits = string.digits
# # random.choice(digits) selects a random digit from string.digits.
# random_string = ''.join(random.choice(digits) for _ in range(6))
# print(random_string, type(random_string))
# print('UUID', uuid.uuid4())

test_dict = {
  'hi': 'hi',
  'you': 'you'
}

print(**test_dict)