# The Python standard library includes some functionality for communicating
# over the Internet.
# However, we will use a more powerful and simpler library called requests.
# This is external library that you may need to install first.


import json
import requests
from typing import Any, Dict, List, Tuple
from collections import defaultdict
from math import isnan
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from datetime import date
from typing import Optional, List, Dict

def get_data() -> Dict[str, Any]:
    """
    Fetch earthquakes as GeoJSON from the USGS FDSN Event API and parse to Python types.

    Returns:
        A Python dict representing the GeoJSON FeatureCollection.
        See USGS GeoJSON doc: features[i].properties.mag; features[i].geometry.coordinates = [lon, lat, depth].
    """
    
    response = requests.get(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        params={
            "format": "geojson",      
            "starttime": "2000-01-01",
            "endtime": "2018-10-11",
            "minlatitude": "50.008",
            "maxlatitude": "58.723",
            "minlongitude": "-9.756",
            "maxlongitude": "1.67",
            "minmagnitude": "1",
            "orderby": "time-asc",    
        },
        timeout=30,
    )
    response.raise_for_status()

    
    data = response.json()  

    
    if not isinstance(data, dict) or "features" not in data:
        raise ValueError("Unexpected response structure (no 'features' in GeoJSON).")

    return data


def count_earthquakes(data: Dict[str, Any]) -> int:
    """Get the total number of earthquakes in the response."""
    
    meta_count = data.get("metadata", {}).get("count")
    features = data.get("features", [])
    return int(meta_count) if isinstance(meta_count, int) else len(features)


def get_magnitude(earthquake: Dict[str, Any]) -> float:
    """Retrieve the magnitude of a single earthquake feature."""
    
    mag = earthquake.get("properties", {}).get("mag", None)
   
    return float(mag) if mag is not None else float("nan")


def get_location(earthquake: Dict[str, Any]) -> Tuple[float, float]:
    """
    Retrieve (latitude, longitude) for a single earthquake feature.

    GeoJSON coordinates are [lon, lat, depth] — we ignore depth here. :contentReference[oaicite:4]{index=4}
    """
    coords = earthquake.get("geometry", {}).get("coordinates", [])
    if not (isinstance(coords, list) and len(coords) >= 2):
        raise ValueError("Earthquake feature missing coordinates.")
    lon, lat = coords[0], coords[1]
    return float(lat), float(lon)


def get_maximum(data: Dict[str, Any]) -> Tuple[float, Tuple[float, float]]:
    """
    Find the strongest earthquake: return (max_magnitude, (lat, lon)).

    Skips features with missing magnitudes (None/NaN).
    """
    features: List[Dict[str, Any]] = data.get("features", [])
    if not features:
        raise ValueError("No earthquake features in data.")

    
    max_feature = None
    max_mag = float("-inf")

    for f in features:
        m = get_magnitude(f)
        if m != m:   
            continue
        if m > max_mag:
            max_mag = m
            max_feature = f

    if max_feature is None:
        raise ValueError("No features contained a valid magnitude.")

    max_loc = get_location(max_feature)
    return max_mag, max_loc



if __name__ == "__main__":
    data = get_data()
    print(f"Loaded {count_earthquakes(data)} earthquakes")
    max_magnitude, max_location = get_maximum(data)
    print(f"The strongest earthquake was at {max_location} with magnitude {max_magnitude}")


def get_year(earthquake: dict) -> int:
    """Extract the calendar year from a USGS earthquake feature."""
   
    
    ts_ms = earthquake.get("properties", {}).get("time")
    if ts_ms is None:
        raise ValueError("Feature has no 'properties.time'.")
    return date.fromtimestamp(ts_ms / 1000).year


def get_magnitudes_per_year(earthquakes: list[dict]) -> dict[int, list[float]]:
    """Group magnitudes by year: {year: [m1, m2, ...]}."""
    by_year: dict[int, list[float]] = defaultdict(list)
    for eq in earthquakes:
        try:
            y = get_year(eq)
        except Exception:
            continue
        by_year[y].append(get_magnitude(eq))
    return dict(by_year)

def plot_number_per_year(
    earthquakes: List[Dict],
    *,
    show: bool = True,
    savepath: Optional[str] = "quakes_count_per_year.png",
):
    """Plot frequency (count) of earthquakes per year; show and/or save."""
    by_year = defaultdict(int)
    for eq in earthquakes:
        try:
            y = get_year(eq)
        except Exception:
            continue
        by_year[y] += 1

    years = sorted(by_year.keys())
    counts = [by_year[y] for y in years]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.bar(years, counts)
    ax.set_title("Number of Earthquakes per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Count")
   
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()

    if savepath:
        fig.savefig(savepath, dpi=150, bbox_inches="tight")  
    if show:  
        plt.show()
    return fig, ax

def plot_average_magnitude_per_year(
     earthquakes: List[Dict],
    *,
    show: bool = True,
    savepath: Optional[str] = "quakes_avg_mag_per_year.png",
):
    """Plot average magnitude per year (ignoring missing magnitudes)."""
    mags_by_year = get_magnitudes_per_year(earthquakes)

    years = sorted(mags_by_year.keys())
    avgs = []
    for y in years:
        mags = [m for m in mags_by_year[y] if not isnan(m)]
        avgs.append(sum(mags) / len(mags) if mags else float("nan"))

    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.plot(years, avgs, marker="o")
    ax.set_title("Average Magnitude per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Average magnitude")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    fig.tight_layout()

    if savepath:
        fig.savefig(savepath, dpi=150, bbox_inches="tight")
    if show:
        plt.show()
    return fig, ax


if __name__ == "__main__":
    data = get_data()
    quakes = data["features"]
    print(f"Loaded {count_earthquakes(data)} earthquakes")
 
    plot_number_per_year(quakes, show=True, savepath="quakes_count_per_year.png")
    
    plt.clf()

    plot_average_magnitude_per_year(quakes, show=True, savepath="quakes_avg_mag_per_year.png")

