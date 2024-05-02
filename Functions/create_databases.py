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

# SQL queries to create tables with existence check
create_tables_queries = {
    "Event_Manager1": [
        """
        CREATE TABLE IF NOT EXISTS Venues (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Name VARCHAR(255),
            City VARCHAR(100),
            Capacity INT,
            Price_per_hour DECIMAL(10,2)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Bookings (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Client_name VARCHAR(255),
            Date DATE,
            Start_time TIME,
            End_time TIME
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS VenueUsed (
            VenueID INT,
            BookingID INT,
            FOREIGN KEY (VenueID) REFERENCES Venues(ID),
            FOREIGN KEY (BookingID) REFERENCES Bookings(ID),
            PRIMARY KEY (VenueID, BookingID)
        );
        """
    ],
    "Event_Manager2": [
        """
        CREATE TABLE IF NOT EXISTS Venues (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Name VARCHAR(255),
            City VARCHAR(100),
            Capacity INT,
            Price_per_hour DECIMAL(10,2)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS Bookings (
            ID INT AUTO_INCREMENT PRIMARY KEY,
            Client_name VARCHAR(255),
            Date DATE,
            Start_time TIME,
            End_time TIME
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS VenueUsed (
            VenueID INT,
            BookingID INT,
            FOREIGN KEY (VenueID) REFERENCES Venues(ID),
            FOREIGN KEY (BookingID) REFERENCES Bookings(ID),
            PRIMARY KEY (VenueID, BookingID)
        );
        """
    ]
}

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
        connection.close()

    except OperationalError as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

def create_tables(database_name):
    try:
        # Establish a connection to the specified database
        connection = pymysql.connect(host=connection_params['host'],
                                     user=connection_params['user'],
                                     password=connection_params['password'],
                                     database=database_name,
                                     cursorclass=pymysql.cursors.DictCursor)
        print(f"Connection established to {database_name}!")

        with connection.cursor() as cursor:
            # Executing each query to create tables
            for query in create_tables_queries[database_name]:
                cursor.execute(query)
                print(f"Query executed successfully in {database_name}")
            connection.commit()

    except OperationalError as e:
        print(f"An error occurred while connecting to {database_name}: {e}")
    finally:
        if connection:
            connection.close()
            print(f"Connection to {database_name} closed.")

# Creating databases
create_databases()

# Creating tables in each database
for db_name in databases:
    create_tables(db_name)
