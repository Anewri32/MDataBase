import os.path
import random
import re
import sqlite3
import string
import cryptocode.myfunctions
from .ExternalFile import File


def handle_exceptions(fun):
    def re_fun(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except Exception as e:
            print(f'Exception handling: {e}')

    return re_fun


def generate_random_characters(length):
    return ''.join(
        random.choices(string.ascii_letters + string.digits + string.punctuation, k=int(length)))


def generate_user(length):
    consonants = 'bcdfghjklmnprstvwxyz'
    vowels = 'aeiou'
    user = random.choice(consonants).upper()  # Choose an initial letter and convert it to uppercase
    length -= 1  # Subtract 1 to account for the initial letter

    for i in range(length):
        if i % 2 == 0:  # Alternate between consonants and vowels
            user += random.choice(vowels)
        else:
            user += random.choice(consonants)
    return user


def extract_user_from_email(email):
    pattern = r"([^@]+)@.*"
    match = re.match(pattern, email)
    if match:
        return match.group(1).capitalize()
    else:
        return None


class DB:
    def __init__(self, data_base, key='hfNdd521@Dfkl'):
        """
        The 'key' parameter encrypts the file containing the automatically generated encryption key '*.key',
        which is used to encrypt the fields called 'password' in the database. Using this
        parameter serves to store a key securely.

        You can assign a custom key when instantiating the class. If the file with the generated key is deleted,
        the encrypted fields cannot be read. When obtaining an encrypted field, you must use the
        'decrypt' method to read it. You can also encrypt data before sending it to the database.
        """
        if '.db' not in data_base:
            data_base += '.db'
        self.__key = key
        self.__data_base = data_base
        self.__connection = sqlite3.connect(data_base)

    @handle_exceptions
    def __get_file_key(self):
        file_key = File(self.__data_base.replace('.db', '.key'), self.__key)
        if os.path.exists(file_key.file):
            return file_key.read()
        else:
            # If the key does not exist, a new one is generated and saved in the external file
            gen_key = generate_random_characters(len(self.__key) ** 1.5)
            file_key.write(gen_key)
            return gen_key

    @property
    def data_base(self):
        return self.__data_base

    @handle_exceptions
    def create_table(self, table_name, fields):
        cursor = self.__connection.cursor()
        fields_str = ', '.join([f'{name} {type}({length})' for name, type, length in fields])
        cursor.execute(
            f'CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {fields_str})')
        self.__connection.commit()

    @handle_exceptions
    def insert_record(self, table_name, data):
        cursor = self.__connection.cursor()
        fields = ', '.join(data.keys())
        values = ', '.join(['?'] * len(data))
        for i in data:
            if i.lower().__eq__('password'):
                data[i] = self.encrypt(data[i])
        cursor.execute(f'INSERT INTO {table_name} ({fields}) VALUES ({values})', list(data.values()))
        self.__connection.commit()

    @handle_exceptions
    def update_record(self, table_name, record_id, new_data):
        cursor = self.__connection.cursor()
        for i in new_data:
            if i.lower().__eq__('password'):
                new_data[i] = self.encrypt(new_data[i])
        new_data_str = ', '.join([f'{name} = ?' for name in new_data.keys()])
        cursor.execute(f'UPDATE {table_name} SET {new_data_str} WHERE id = ?',
                       list(new_data.values()) + [record_id])
        self.__connection.commit()

    @handle_exceptions
    def get_record_by_value(self, table_name, column_name, value):
        cursor = self.__connection.cursor()
        cursor.execute(f'SELECT * FROM {table_name} WHERE {column_name} = ?', [value])
        columns = [col[0] for col in cursor.description]
        records = cursor.fetchall()
        result = []
        for record in records:
            result.append({columns[i]: record[i] for i in range(len(columns))})
        return result

    @handle_exceptions
    def get_record_by_id(self, table_name, record_id):
        cursor = self.__connection.cursor()
        cursor.execute(f'SELECT * FROM {table_name} WHERE id = ?', [record_id])
        columns = [col[0] for col in cursor.description]
        record = cursor.fetchone()
        if record:
            return {columns[i]: record[i] for i in range(len(columns))}
        else:
            return None

    @handle_exceptions
    def delete_field(self, table_name, field_name):
        cursor = self.__connection.cursor()
        cursor.execute(f'ALTER TABLE {table_name} DROP COLUMN {field_name}')
        self.__connection.commit()

    @handle_exceptions
    def delete_record_by_id(self, table_name, record_id):
        cursor = self.__connection.cursor()
        cursor.execute(f'DELETE FROM {table_name} WHERE id = ?', [record_id])
        self.__connection.commit()

    def generate_email(self, table, field='email'):
        while True:
            email = generate_user(5).lower() + '@example.com'
            cursor = self.__connection.cursor()
            try:
                # It will be checked that the generated email does not exist in the database, exceptions here
                # indicate that the table or the searched email was not found.
                cursor.execute(f'SELECT * FROM {table} WHERE {field} = ?', [email])
            except Exception as e:
                print(f'Email generator ({self.data_base})...{e}')
                pass
            if not cursor.fetchone():
                return email

    def encrypt(self, data):
        return cryptocode.myfunctions.encrypt(data, self.__get_file_key())

    def decrypt(self, data):
        return cryptocode.myfunctions.decrypt(data, self.__get_file_key())


"""
# Example of usage:
database = DB('prueba.db')

fields = [('name', 'TEXT', 50), ('last_name', 'TEXT', 50), ('age', 'INTEGER', 50), ('email', 'TEXT', 100),
          ('password', 'TEXT', 100)]
database.create_table('users', fields)

email = database.generate_email('users')
user = extract_user_from_email(email)
database.insert_record('users', {'name': user, 'last_name': 'nunez', 'age': 20, 'email': email,
                                 'password': '5252525252'})

# Returns a list containing the records, each record is a dictionary
records = database.get_record_by_value('users', 'last_name', 'nunez')
print('Records obtained by their values are', records)

for i in records:
    # i will be equal to a dictionary, it contains the data of the obtained record
    print(i)
    new_record_id = i['id']
    password = database.decrypt(i['password'])
    print('The encrypted password: ' + i['password'])
    print('The decrypted password is: ' + password)
    database.update_record('users', new_record_id, {'age': 41, 'password': '42424242'})
    obtained_record = database.get_record_by_id('users', new_record_id)
    print("Record obtained by ID:", obtained_record)
    print('The encrypted password: ' + obtained_record["password"])
    password = database.decrypt(obtained_record["password"])
    print('The decrypted password is: ' + password)
"""