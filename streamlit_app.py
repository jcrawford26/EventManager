import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px

def connect_to_db():
    db_info = st.secrets["connections"]["mysql"]
    connection = pymysql.connect(
        host=db_info["host"],
        user=db_info["username"],
        password=db_info["password"],
        database=db_info["database"],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@st.cache(hash_funcs={pymysql.connections.Connection: id}, allow_output_mutation=True, ttl=600)
def fetch_data(query, parameters=None):
    with connect_to_db() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
            result = cursor.fetchall()
    return pd.DataFrame(result)

def plot_venue_counts_per_city():
    query = "SELECT City, COUNT(*) AS venue_count FROM Venues GROUP BY City;"
    df = fetch_data(query)
    fig = px.bar(df, x='City', y='venue_count', title="Venue Counts per City")
    st.plotly_chart(fig)

def app_layout():
    st.title('EventManager - Explore Venues')
    
    with st.sidebar:
        st.write("## Filters")
        city = st.text_input("City", "")
        capacity = st.number_input("Minimum Capacity", min_value=0, value=0)
        price_range = st.slider("Price Range Per Hour", 0, 500, (50, 300))
    
    if st.sidebar.button('Show Venues'):
        query = '''
        SELECT * FROM Venues 
        WHERE (%s = '' OR City = %s) AND 
              Capacity >= %s AND 
              Price_per_hour BETWEEN %s AND %s
        ORDER BY Price_per_hour DESC;
        '''
        parameters = (city, city, capacity, price_range[0], price_range[1])
        venues_df = fetch_data(query, parameters)
        if not venues_df.empty:
            st.write("### Venues Matching Criteria")
            st.dataframe(venues_df)
        else:
            st.write("No venues match your criteria.")
    
    st.write("### General Venue Insights")
    plot_venue_counts_per_city()

app_layout()
