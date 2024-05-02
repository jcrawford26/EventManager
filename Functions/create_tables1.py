# IMPORT LIBRARIES
import sys
import pymysql
from pymysql.err import OperationalError

# OPTION 2: PyMySQL
# Replace the placeholders with the actual database connection details
EventManager1_Connection_Params = {
    'host': 'localhost',
    'user': 'dsci551',
    'password': 'Dsci-551',
    'database': 'Event_Manager1'
}

EventManager2_Connection_Params = {
    'host': 'localhost',
    'user': 'dsci551',
    'password': 'Dsci-551',
    'database': 'Event_Manager2'
}

# List of connection parameters for easy iteration
connections_params = [EventManager1_Connection_Params, EventManager2_Connection_Params]

# SQL queries to create tables with existence check
create_tables_queries = [
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


# Function to execute creation queries on a database
def create_tables_in_database(connection_params):
    try:
        # Establishing a connection to the database
        connection = pymysql.connect(host=connection_params['host'],
                                     user=connection_params['user'],
                                     password=connection_params['password'],
                                     database=connection_params['database'],
                                     cursorclass=pymysql.cursors.DictCursor)
        print(f"Connection established to {connection_params['database']}!")

        with connection.cursor() as cursor:
            # Executing each query to create tables
            for query in create_tables_queries:
                cursor.execute(query)
                print(f"Query executed successfully in {connection_params['database']}")
            connection.commit()

    except OperationalError as e:
        print(f"An error occurred while connecting to {connection_params['database']}: {e}")
    finally:
        if connection:
            connection.close()
            print(f"Connection to {connection_params['database']} closed.")


# Iterating through each database to create tables
for params in connections_params:
    create_tables_in_database(params)
