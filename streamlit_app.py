import streamlit as st
import pymysql
import pandas as pd

def connect_to_db():
    db_info = st.secrets["connections"]["mysql"]
    return pymysql.connect(
        host=db_info["host"],
        user=db_info["username"],
        password=db_info["password"],
        database=db_info["database"],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def fetch_venues_by_city(city):
    connection = connect_to_db()
    query = f"SELECT * FROM Venues WHERE City = '{city}';"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

def fetch_venues_capacity_over(capacity):
    connection = connect_to_db()
    query = f"SELECT * FROM Venues WHERE Capacity > {capacity};"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

def fetch_venues_ordered_by_price():
    connection = connect_to_db()
    query = "SELECT * FROM Venues ORDER BY Price_per_hour DESC;"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

def fetch_average_price():
    connection = connect_to_db()
    query = "SELECT AVG(Price_per_hour) AS average_price FROM Venues;"
    df = pd.read_sql(query, connection)
    connection.close()
    return df.iloc[0]['average_price']

def fetch_venue_counts_per_city():
    connection = connect_to_db()
    query = "SELECT City, COUNT(*) AS venue_count FROM Venues GROUP BY City;"
    df = pd.read_sql(query, connection)
    connection.close()
    return df

# Example of using Plotly for visualization within Streamlit
def plot_venue_counts_per_city():
    df = fetch_venue_counts_per_city()
    fig = px.bar(df, x='City', y='venue_count', title="Venue Counts per City")
    st.plotly_chart(fig)

# Incorporating into Streamlit interface
st.title('EventManager')
st.write("### Venues Ordered by Price Per Hour")
st.dataframe(fetch_venues_ordered_by_price())
st.write("### Average Price Per Hour Across All Venues")
st.write(fetch_average_price())
plot_venue_counts_per_city()
