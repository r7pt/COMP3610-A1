import streamlit as st
#python -m streamlit run app.py
import pandas as pd
import numpy as np
import duckdb as db
import matplotlib.pyplot as plt
import seaborn as sns
import polars as pl
import plotly.express as px
from matplotlib.patches import Patch


st.set_page_config( page_title='NYC Taxi Dashboard', page_icon='taxi', layout='wide' ) 

st.title('NYC Taxi Trip Dashboard') 

@st.cache_data 
def load_data(): 
    df = pd.read_parquet("yellow_taxi_data.parquet")
    return df

df= load_data()
df2 = pd.read_csv("taxi_zone_data.csv")
tab1, tab2, tab3 ,tab4, tab5,tab6, tab7, tab8 ,tab9, tab10= st.tabs([" total trips", "average fare", "total revenue","average trip distance","average trip duration.","bar chart-total trip","line chart","bar graph","histogram","heatmap"])
db = db.connect()

with tab1:
    
    rows,columns = df.shape
    st.metric("total trips", rows, delta=None, delta_color="normal", help=None, label_visibility="visible", border=False, width="stretch", height="content", chart_data=None, chart_type="line", delta_arrow="auto", format=None)

with tab2:

    avg_fare = df.loc[:,"fare_amount"].mean()
    st.metric("average fare", avg_fare, delta=None, delta_color="normal", help=None, label_visibility="visible", border=False, width="stretch", height="content", chart_data=None, chart_type="line", delta_arrow="auto", format=None)

with tab3:
  
    total_revenue = df.loc[:,"total_amount"].sum()
    st.metric("total revenue", total_revenue, delta=None, delta_color="normal", help=None, label_visibility="visible", border=False, width="stretch", height="content", chart_data=None, chart_type="line", delta_arrow="auto", format=None)

with tab4:
    avg_trip_distance = df.loc[:,"trip_distance"].mean()
    st.metric("average trip distance", avg_trip_distance, delta=None, delta_color="normal", help=None, label_visibility="visible", border=False, width="stretch", height="content", chart_data=None, chart_type="line", delta_arrow="auto", format=None)

with tab5:
    df['trip duration'] = df["tpep_dropoff_datetime"] - df["tpep_pickup_datetime"]
    avg_trip_duration = str(df.loc[:,"trip duration"].mean())
    st.metric("average trip duration", avg_trip_duration, delta=None, delta_color="normal", help=None, label_visibility="visible", border=False, width="stretch", height="content", chart_data=None, chart_type="line", delta_arrow="auto", format=None)

with tab6:

    result = db.execute(''' 
                    SELECT c.Zone AS pickup_name,
                    COUNT(*) as total_trips
                    FROM 'yellow_taxi_data.parquet' as p
                    JOIN 'taxi_zone_data.csv' as c
                    ON p.PULocationID = c.LocationID
                    GROUP BY c.Zone
                    ORDER BY total_trips DESC
                    LIMIT 10
            ''').fetchdf()

    fig = px.bar(
    result,
    x="pickup_name",
    y="total_trips"
    )

    num_trips=result["total_trips"]


    colors = [
    "#2FA82B" if t > 140000 else
    "#2C3E50" if 100000 <= t < 140000 else
    "#E74C3C" 
    for t in (num_trips)
    ]


    plt.figure(figsize=(28,15))
    plt.rcParams['axes.axisbelow'] = True
    plt.grid()
    bars =plt.bar(result["pickup_name"],result["total_trips"],color=colors,edgecolor='white')
    plt.xlabel('Pickup Zones', fontsize=12)
    plt.ylabel('Number of Trips', fontsize=12)
    plt.title('NYC Taxi trips by location', fontsize=14)
    plt.xticks(range(10))


    legend_elements = [
        Patch(facecolor='#2FA82B', label='trips greater than 140000'),
        Patch(facecolor='#2C3E50', label='trips between 100000 and 140000 '),
        Patch(facecolor='#E74C3C', label='trips less than 100000')
    ]
    plt.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    st.plotly_chart(fig, on_select="rerun")
    st.write("From the data we can see that places with the hightest total trip were either those of airports, entertainment centers or commercial districts. Due to the high population density such apartments, malls and workspace, this indicates that most people dont own cars and that popular distinations are in relative close - proxcitmity, with airport being expected for taxi uasge as traveller dont have to worry about paying a vehicle fee at the airport. this may also be influenced that new york is a popular tourist attraction")
    

with tab7:
    result2 = db.execute('''
                     SELECT 
                     EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour,
                     AVG(fare_amount) AS avg_fare
                     FROM 'yellow_taxi_data.parquet' 
                     GROUP BY hour
                     ORDER BY hour ASC
                     ''').fetchdf()
    #print(result2)
    
    selectedhour = st.slider("the hour ", 0, 23,(0,23))
    st.write("u have selected ", selectedhour)
     
    filtered =result2[(result2["hour"]>=selectedhour[0]) &( result2["hour"]<= selectedhour[1])]
    fig = px.line(result2,x="hour",y="avg_fare",title="New York taxi average fare",labels={'hour': 'Hour', 'avg_fare': 'Average fares'})

    fig.update_traces(mode='lines', hovertemplate='%{x}<br>Trips: %{y:,}')
    fig.update_layout(height=500, hovermode='x unified')
    fig.update_xaxes(
    tickmode='linear',
    tickvals=list(range(23))
)

    st.plotly_chart(fig, on_select="rerun")
    st.write("From the data we can observed that early hours in the morning there is the lowest taxi fare which either implies that there is a low number of trips or reduced number of taxis. the highest fares were observed at the 5th hour which the decreses to around the 8th hour this implies that memeber of the workforce are departing to their workspaces resulting in more trips and a higher fare for thoes hours, to enforce this there is an increases from the 13th hour where employees are finishing shifts, there is a decrease till 18th hour where a rise in fairs occur indicating that people are heading out to part-take in recreational activities")

with tab8:
    options = ["Credit card", "Cash", "No charge", "Dispute", "Unknown"]
    mapping = {option: i+1 for i, option in enumerate(options)}

    result3 = db.execute('''
                     SELECT payment_type,
                     count(*) * 100 / sum(count(*)) OVER() as percentage,
                     FROM 'yellow_taxi_data.parquet'
                     GROUP BY payment_type
                     ORDER BY percentage DESC
                     ''').fetchdf()
    
    options = st.multiselect("selct the payment types",options,placeholder="Select payment method...")
    if options==[]:
        fig =px.bar(result3, x="payment_type", y="percentage")
    else:
        loc=[]
        for option in options:
            loc.append(mapping.get(option))
        
        filtered =result3[(result3["payment_type"].isin(loc))]

        fig =px.bar(filtered, x="payment_type", y="percentage")
   
    st.plotly_chart(fig, on_select="rerun")
    st.write("From the data, we can observe that the most common payment types was cash being 78% this implies that most of majority of the population in new york uses cash payment rather than credit and if this can be implied to many other transaction in the city, as if for small payments such as taxi fares they use cash . ")

with tab9:

    df55 = df[["trip_distance"]]
    df55 = df55[df55["trip_distance"] > 0]
    df55 = df55[df55["trip_distance"] < 50]

    df55["trip_distance"] = df55["trip_distance"].round()

    #print(df55["trip_distance"].var())

    figg = px.histogram(df55,x="trip_distance",nbins=50,title="Distribution of Trip Distances")
    st.plotly_chart(figg, on_select="rerun")
    st.write("From the dat we can see that more than 80& of trips occurred with in 5 miles of the pickup location.The large number of short trips implies that these distination are relativitly close, which is also enforced by New York's high population due to are apartment building and commerical buildings making everything in close - range and that user of taxis dont usually far from their homes and stay within their community majority of the time")


with tab10:

    
    #df=df.with_columns(pl.col("tpep_pickup_datetime").dt.hour().alias("pickup_hour"))
    df["pickup_hour"] = pd.to_datetime(df["tpep_pickup_datetime"]).dt.hour
    df["pickup_day_of_week"] = pd.to_datetime(df["tpep_pickup_datetime"]).dt.day_name()
    pdf = df[["pickup_day_of_week","pickup_hour"]]

    order_week = [ 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ordered = pd.CategoricalDtype(categories=order_week,ordered=True)
    pdf["pickup_day_of_week"] = pdf["pickup_day_of_week"].astype(ordered)

    p=pdf.groupby(["pickup_day_of_week","pickup_hour"]).value_counts()
    p=p.reset_index(name="trip_count")
    g=p.pivot(index="pickup_day_of_week",columns="pickup_hour",values="trip_count")
    #print(p)

    fig=px.imshow(g)
    st.plotly_chart(fig, on_select="rerun")
    st.write("From the data, we can observe that the trips occur at 4 - 6 in the morning on week days while on weekends higher trip occurrence at later hours susch as 6 -8  but with less overall trips and gradually reduces during the day with the least trip occuring at weekday 18 hour. this imples that member of the workforce are goin to their palce of work at during the weekday and during the weekend citzens may be going to recreational activities ")


#python -m streamlit run app.py