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
    # Build request (the API defaults to QuakeML; request GeoJSON explicitly)
    response = requests.get(
        "https://earthquake.usgs.gov/fdsnws/event/1/query",
        params={
            "format": "geojson",      # ask for GeoJSON explicitly
            "starttime": "2000-01-01",
            "endtime": "2018-10-11",
            "minlatitude": "50.008",
            "maxlatitude": "58.723",
            "minlongitude": "-9.756",
            "maxlongitude": "1.67",
            "minmagnitude": "1",
            "orderby": "time-asc",    # oldest first; we will compute max ourselves
            # You could also request orderby=magnitude&limit=1 to let the API sort by magnitude,
            # but the exercise asks you to process the data yourself.
        },
        timeout=30,
    )
    response.raise_for_status()

    # Parse the GeoJSON (text -> Python dict)
    data = response.json()  # same as json.loads(response.text)

    # Optional sanity checks (match the documented structure)
    if not isinstance(data, dict) or "features" not in data:
        raise ValueError("Unexpected response structure (no 'features' in GeoJSON).")

    return data


def count_earthquakes(data):
    """Get the total number of earthquakes in the response."""
    # Either read metadata.count or len(features). Both should agree for a full response.
    # USGS GeoJSON defines metadata.count and features[]. :contentReference[oaicite:2]{index=2}
    meta_count = data.get("metadata", {}).get("count")
    features = data.get("features", [])
    return int(meta_count) if isinstance(meta_count, int) else len(features)


def get_magnitude(earthquake):
    """Retrieve the magnitude of a single earthquake feature."""
    # properties.mag is documented as a decimal; it may be None for some events. :contentReference[oaicite:3]{index=3}
    mag = earthquake.get("properties", {}).get("mag", None)
    # Some events can have missing/None magnitudes; normalize to float('nan') to make comparisons safe.
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
        if m != m:   # NaN check
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
