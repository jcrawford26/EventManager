# IMPORT LIBRARIES
import sys
import pymysql
from pymysql.err import OperationalError
import hashlib

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


# Generic hash function to choose the database based on any string input
def choose_database(input_string):
    # Create a hash of the input string
    hash_object = hashlib.sha256(input_string.encode())
    hash_digest = hash_object.hexdigest()
    # Determine the target database using the hash value
    if int(hash_digest, 16) % 2 == 0:
        return EventManager1_Connection_Params
    else:
        return EventManager2_Connection_Params


# Existing functions and connection parameters...

def add_venue(venue_name, city, capacity, price_per_hour):
    # Choose the target database based on the venue name
    connection_params = choose_database(venue_name)

    try:
        # Connect to the database
        connection = pymysql.connect(host=connection_params['host'],
                                     user=connection_params['user'],
                                     password=connection_params['password'],
                                     database=connection_params['database'],
                                     cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            # Check if the venue already exists
            cursor.execute("SELECT ID FROM Venues WHERE Name = %s", (venue_name,))
            if cursor.fetchone() is None:
                # Insert the new venue if it doesn't exist
                cursor.execute("INSERT INTO Venues (Name, City, Capacity, Price_per_hour) VALUES (%s, %s, %s, %s)",
                               (venue_name, city, capacity, price_per_hour))
                connection.commit()
                print(f"Venue '{venue_name}' added successfully.")
            else:
                print(f"Venue '{venue_name}' already exists.")
    except pymysql.err.OperationalError as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()


# Don't forget to define or import your choose_database function if it's not already included above

if __name__ == "__main__":
    if len(sys.argv) == 5:
        # Extracting arguments
        venue_name, city, capacity_str, price_per_hour_str = sys.argv[1:]
        try:
            # Converting string arguments to appropriate types
            capacity = int(capacity_str)
            price_per_hour = float(price_per_hour_str)
            # Call the add_venue function with command line arguments
            add_venue(venue_name, city, capacity, price_per_hour)
        except ValueError as e:
            print(f"Error converting capacity or price_per_hour to number: {e}")
    else:
        print("Usage: python3 add_venue.py 'venue_name' 'city' capacity price_per_hour")
