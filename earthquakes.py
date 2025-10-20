# The Python standard library includes some functionality for communicating
# over the Internet.
# However, we will use a more powerful and simpler library called requests.
# This is external library that you may need to install first.
import json
import requests



def get_data():
    """
    Fetch earthquakes as GeoJSON from the USGS FDSN Event API and parse to Python types.

    Returns:
        A Python dict representing the GeoJSON FeatureCollection.
        See USGS GeoJSON doc: features[i].properties.mag; features[i].geometry.coordinates = [lon, lat, depth].
    """
    
    response = requests.get(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        params={
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


def count_earthquakes(data):
    """Get the total number of earthquakes in the response."""

    meta_count = data.get("metadata", {}).get("count")
    features = data.get("features", [])
    return int(meta_count) if isinstance(meta_count, int) else len(features)


def get_magnitude(earthquake):
    """Retrieve the magnitude of a single earthquake feature."""
  
    mag = earthquake.get("properties", {}).get("mag", None)
   
    return float(mag) if mag is not None else float("nan")


def get_location(earthquake) :
    """
    Retrieve (latitude, longitude) for a single earthquake feature.

    GeoJSON coordinates are [lon, lat, depth] — we ignore depth here. :contentReference[oaicite:4]{index=4}
    """
    coords = earthquake.get("geometry", {}).get("coordinates", [])
    if not (isinstance(coords, list) and len(coords) >= 2):
        raise ValueError("Earthquake feature missing coordinates.")
    lon, lat = coords[0], coords[1]
    return float(lat), float(lon)


def get_maximum(data) :
    """
    Find the strongest earthquake: return (max_magnitude, (lat, lon)).

    Skips features with missing magnitudes (None/NaN).
    """
    features: List[Dict[str, Any]] = data.get("features", [])
    if not features:
        raise ValueError("No earthquake features in data.")

    # Compute argmax by magnitude, ignoring missing values
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


# Run the analysis
if __name__ == "__main__":
    data = get_data()
    print(f"`The number of loaded {count_earthquakes(data)} earthquakes")
    max_magnitude, max_location = get_maximum(data)
    print(f"The strongest earthquake was at {max_location} with the magnitude {max_magnitude}")
