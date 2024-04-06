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

def fetch_data(query, parameters=None):
    connection = connect_to_db()
    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        result = cursor.fetchall()
    connection.close()
    return pd.DataFrame(result)

def app_layout():
    st.title('EventManager - Explore Venues')
    tab1, tab2, tab3 = st.tabs(["Venue Overview", "Detailed Visualizations", "Analytics"])
    
    with tab1:
        city = st.text_input("City", "")
        capacity = st.number_input("Minimum Capacity", min_value=0, value=0)
        price_range = st.slider("Price Range Per Hour", 2000, 10000, (4000, 7000))
        
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
    
    with tab2:
        st.write("## Visualizations")
        # Visualization 1: Distribution of venue capacities
        df_capacity = fetch_data("SELECT Capacity FROM Venues;")
        fig_capacity = px.histogram(df_capacity, x="Capacity", title="Distribution of Venue Capacities")
        st.plotly_chart(fig_capacity)
        
        # Visualization 2: Average price per hour by city
        query_price_by_city = "SELECT City, AVG(Price_per_hour) as Avg_Price FROM Venues GROUP BY City;"
        df_price_by_city = fetch_data(query_price_by_city)
        fig_price_by_city = px.bar(df_price_by_city, x="City", y="Avg_Price", title="Average Price Per Hour by City")
        st.plotly_chart(fig_price_by_city)
    
    with tab3:
        st.write("## Analytics")
        # Analytics 1: Average capacity by city
        query_avg_capacity = "SELECT City, AVG(Capacity) as Avg_Capacity FROM Venues GROUP BY City;"
        df_avg_capacity = fetch_data(query_avg_capacity)
        col1, col2 = st.columns(2)
        with col1:
            st.write("### Average Capacity by City")
            st.dataframe(df_avg_capacity)
        # Analytics 2: Count of venues by city
        query_count_by_city = "SELECT City, COUNT(*) as Venue_Count FROM Venues GROUP BY City;"
        df_count_by_city = fetch_data(query_count_by_city)
        with col2:
            st.write("### Count of Venues by City")
            st.dataframe(df_count_by_city)

app_layout()
