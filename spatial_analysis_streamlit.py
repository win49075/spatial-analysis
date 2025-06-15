import pandas as pd
import requests
import time
import folium
from scipy.stats import gaussian_kde
import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

st.title("Spatial Analysis Tool: Elevation & KDE Heatmap")

uploaded_file = st.file_uploader("Upload your CSV file with Latitude and Longitude", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    df = df[pd.to_numeric(df["Latitude"], errors="coerce").notnull()]
    df = df[pd.to_numeric(df["Longitude"], errors="coerce").notnull()]
    df["Latitude"] = df["Latitude"].astype(float)
    df["Longitude"] = df["Longitude"].astype(float)

    st.subheader("Sample Data")
    st.dataframe(df.head())

    def get_elevation(lat, lng):
        url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lng}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()["results"][0]["elevation"]
        except:
            return None
        return None

    if st.button("Get Elevation Data"):
        elevations = []
        progress = st.progress(0)
        for idx, row in enumerate(df.itertuples()):
            elevations.append(get_elevation(row.Latitude, row.Longitude))
            time.sleep(1)
            progress.progress((idx + 1) / len(df))
        df["Elevation (m)"] = elevations
        st.success("Elevation data added!")
        st.dataframe(df.head())

    st.subheader("Interactive Map")
    if "Elevation (m)" in df.columns:
        m = folium.Map(location=[df["Latitude"].mean(), df["Longitude"].mean()], zoom_start=11)
        for _, row in df.iterrows():
            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                popup=f"Elevation: {row['Elevation (m)']} m"
            ).add_to(m)
        from streamlit_folium import folium_static
        folium_static(m)

    st.subheader("Spatial Distribution Heatmap (KDE)")
    coords = df[["Longitude", "Latitude"]].to_numpy().T
    kde = gaussian_kde(coords)
    density = kde(coords)

    fig, ax = plt.subplots(figsize=(10, 6))
    scatter = ax.scatter(df["Longitude"], df["Latitude"], c=density, s=50, cmap='viridis')
    fig.colorbar(scatter, label='Location Density')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title("Spatial Distribution Density (KDE)")
    ax.grid(True)
    st.pyplot(fig)

    if "Elevation (m)" in df.columns:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV with Elevation", csv, "output_with_elevation.csv", "text/csv")