import pymysql
from pymysql.err import OperationalError

# Connection parameters
connection_params = {
    'host': 'localhost',
    'user': 'dsci551',
    'password': 'Dsci-551'
}

# Database names to be created
databases = ["Event_Manager1", "Event_Manager2"]

def create_databases():
    try:
        # Connect without specifying a database to allow creation if it does not exist
        connection = pymysql.connect(host=connection_params['host'],
                                     user=connection_params['user'],
                                     password=connection_params['password'],
                                     cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            for database in databases:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
                print(f"Database {database} created or already exists.")

    except OperationalError as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

# Creating databases
create_databases()

