import sys
import pymysql
from pymysql.err import OperationalError
import hashlib

# Connection parameters for both databases
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

def find_venues_by_city_and_budget(city, max_budget):
    all_venues = []  # To aggregate venues from all databases

    for connection_params in connections_params:
        try:
            # Connect to the current database
            connection = pymysql.connect(host=connection_params['host'],
                                         user=connection_params['user'],
                                         password=connection_params['password'],
                                         database=connection_params['database'],
                                         cursorclass=pymysql.cursors.DictCursor)

            with connection.cursor() as cursor:
                # Query for venues in the specified city with a price_per_hour less than or equal to the max_budget
                cursor.execute("""
                    SELECT Name, City, Capacity, Price_per_hour FROM Venues
                    WHERE City = %s AND Price_per_hour <= %s
                """, (city, max_budget))

                venues = cursor.fetchall()

                if venues:
                    all_venues.extend(venues)  # Add the results from the current database to the aggregate list

        except pymysql.err.OperationalError as e:
            print(f"An error occurred while querying {connection_params['database']}: {e}")
        finally:
            if connection:
                connection.close()

    # Display aggregated venues
    if all_venues:
        print(f"Venues in {city} under budget {max_budget}:")
        for venue in all_venues:
            print(f"Name: {venue['Name']}, Capacity: {venue['Capacity']}, Price per hour: {venue['Price_per_hour']}")
    else:
        print(f"No venues found in {city} under budget {max_budget}.")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        city = sys.argv[1]
        max_budget_str = sys.argv[2]

        try:
            # Convert max_budget to a float to handle budget values properly
            max_budget = float(max_budget_str)
            find_venues_by_city_and_budget(city, max_budget)
        except ValueError as e:
            print(f"Error: Invalid budget value. Please enter a numeric value for the budget. {e}")
    else:
        print("Usage: python3 script_name.py 'city' max_budget")