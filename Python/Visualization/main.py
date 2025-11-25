from fastapi import FastAPI, Query
import pandas as pd
import numpy as np
import plotly.express as px
from fastapi.responses import HTMLResponse

app = FastAPI()

# Load CSV
df = pd.read_csv("Oceanography.csv") 

# List of valid parameters
PARAMETERS = ["DIC", "MLD", "PCO2_ORIGINAL", "CHL", "NO3", "SSS", "SST", "DEVIANT_UNCERTAINTY"]

# Units mapped to parameters
UNITS = {
    "DIC" : "milimole/m3",
    "MLD" : "m",
    "PCO2_ORIGINAL" : "micro_atm",
    "CHL" : "kg/m3",
    "NO3" : "milimole/m3",
    "SSS" : "PSU",
    "SST" : "deg C",
    "DEVIANT_UNCERTAINITY" : "micro atm" 
}


def get_nearest_row(LAT, LON):
    """
    Finds the nearest LAT/LON pair in your CSV.
    Uses Euclidean distance.
    """
    df["dist"] = np.sqrt((df["LAT"] - LAT)**2 + (df["LON"] - LON)**2)
    nearest_index = df["dist"].idxmin()
    return df.iloc[nearest_index]


@app.get("/get_value")
def get_value(
    LAT: float,
    LON: float,
    parameter: str = Query(..., enum=PARAMETERS)
):
    # Find the nearest geographical point
    row = get_nearest_row(LAT, LON)

    # Extract value from CSV
    value = row[parameter]

    # Get proper unit
    unit = UNITS.get(parameter, "")

    return {
        "input_lat": LAT,
        "input_lon": LON,
        "nearest_data_lat": float(row["LAT"]),
        "nearest_data_lon": float(row["LON"]),
        "parameter": parameter,
        "value": float(value),
        "unit": unit
    }

 # BUBBLE MAP VISUALIZATION
@app.get("/map", response_class=HTMLResponse)
def generate_map(parameter: str = Query(..., enum=PARAMETERS)):
    fig = px.scatter_geo(
        df,
        lon="LON",
        lat="LAT",
        color=parameter,
        size=None,  # You can use size=parameter if you want bubble size also
        hover_data=PARAMETERS,
        projection="natural earth",
        title=f"Bubble Map of {parameter}"
    )

    fig.update_geos(
        showcountries=True,
        lataxis_range=[0, 30],    # Limits around India ocean
        lonaxis_range=[40, 100]
    )

    html = fig.to_html(full_html=True)
    return HTMLResponse(content=html)