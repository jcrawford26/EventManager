import streamlit as st

# Access secrets
mysql_secrets = st.secrets["connections"]["mysql"]

dialect = mysql_secrets["dialect"]
host = mysql_secrets["host"]
port = mysql_secrets["port"]
database = mysql_secrets["database"]
username = mysql_secrets["username"]
password = mysql_secrets["password"]

# Use these variables to set up your database connection

# Function to fetch data from the database
def fetch_data():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        query = "SELECT * FROM Venues"  # Replace with your actual table name
        cursor.execute(query)
        result = cursor.fetchall()
    connection.close()
    return pd.DataFrame(result)

# Displaying data in the Streamlit app
if st.button('Show Data'):
    st.write('Fetching data from database...')
    data_df = fetch_data()
    if not data_df.empty:
        st.write(data_df)
    else:
        st.write("No data found.")
