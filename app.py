import streamlit as st
import pandas as pd
import folium
from folium.plugins import HeatMap
import matplotlib.pyplot as plt
import seaborn as sns
from streamlit_folium import folium_static
from google.cloud import bigquery
from google.oauth2 import service_account
import json

# Load secrets from Streamlit Cloud
credentials_info = json.loads(st.secrets["gcp_service_account"])
credentials = service_account.Credentials.from_service_account_info(credentials_info)

@st.cache_data
def load_data():
    project_id = credentials_info["project_id"]
    dataset_id = "crash_analysis"
    table_id = "processed_crash_data"
    client = bigquery.Client(credentials=credentials, project=project_id)

    query = f"SELECT * FROM `{project_id}.{dataset_id}.{table_id}`"
    df = client.query(query).to_dataframe()
    return df

df = load_data()

st.sidebar.title("Filters")
collision_types = df["COLLISIONTYPE"].unique()
selected_collision_type = st.sidebar.selectbox("Select Collision Type", ["All"] + list(collision_types))

df['Year'] = pd.to_datetime(df['CRASHDATETIME']).dt.year
years = sorted(df['Year'].unique())

if len(years) > 1:
    selected_year = st.sidebar.slider(
        "Select Year Range",
        min_value=int(min(years)),
        max_value=int(max(years)),
        value=(int(min(years)), int(max(years)))
    )
    df = df[(df['Year'] >= selected_year[0]) & (df['Year'] <= selected_year[1])]
else:
    st.sidebar.write(f"Only data from {years[0]} is available.")

severity_options = ["All", "Fatal", "Non-Fatal"]
selected_severity = st.sidebar.selectbox("Select Severity", severity_options)

if selected_collision_type != "All":
    df = df[df["COLLISIONTYPE"] == selected_collision_type]

if selected_severity == "Fatal":
    df = df[df["FATALINJURIES"] > 0]
elif selected_severity == "Non-Fatal":
    df = df[df["FATALINJURIES"] == 0]

st.title("San Jose Crash Data Analysis 🚗💥")

st.subheader("📊 Interactive Looker Studio Report")
looker_url = "https://lookerstudio.google.com/embed/reporting/99463f0c-69ac-4c8f-a1b4-a759f2f7ae0a/page/iUI4E"
st.markdown(f'<iframe width="800" height="500" src="{looker_url}" frameborder="0" allowfullscreen></iframe>', unsafe_allow_html=True)

st.subheader("Crash Data Overview")
st.write(df.describe())

st.subheader("Top 5 Collision Types")
fig, ax = plt.subplots(figsize=(8,4))
sns.countplot(y=df["COLLISIONTYPE"], order=df["COLLISIONTYPE"].value_counts().index[:5], ax=ax)
st.pyplot(fig)

st.subheader("Crashes Over Time")
df['YearMonth'] = pd.to_datetime(df['CRASHDATETIME']).dt.to_period('M')
crashes_over_time = df.groupby('YearMonth').size()

fig2, ax2 = plt.subplots(figsize=(10,5))
crashes_over_time.plot(kind='line', marker='o', ax=ax2)
ax2.set_title("Trend of Crashes Over Time in San Jose")
ax2.set_xlabel("Year-Month")
ax2.set_ylabel("Number of Crashes")
st.pyplot(fig2)

st.subheader("Crash Locations Heatmap")
m = folium.Map(location=[df['LATITUDE'].mean(), df['LONGITUDE'].mean()], zoom_start=12)
heat_data = list(zip(df['LATITUDE'], df['LONGITUDE']))
HeatMap(heat_data).add_to(m)
folium_static(m)