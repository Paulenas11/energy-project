import os
import pickle
import hashlib
import pandas as pd

# Base directory where all cached files will be stored.
# Structure:
#   cache/
#       prices/
#       generation/
#       forecast/
#       flows/
#       dataset/
CACHE_DIR = "cache"


def _ensure_dir(path):
    """
    Ensure that a directory exists.
    If it does not exist, create it.

    This is used for:
        - main cache directory
        - subdirectories for each data type (prices, generation, etc.)
    """
    if not os.path.exists(path):
        os.makedirs(path)


def _make_cache_key(function_name, start, end, zone):
    """
    Create a stable, deterministic cache key for a given request.

    Why this is needed:
        - start/end can be strings, timestamps, with or without timezone
        - we normalize them to timezone-naive timestamps
        - we convert them to YYYYMMDDHH format to avoid mismatches
        - we hash the final string to avoid extremely long filenames

    Parameters:
        function_name (str): e.g. "prices", "generation", "dataset"
        start (str or Timestamp)
        end (str or Timestamp)
        zone (str): bidding zone or country code

    Returns:
        str: MD5 hash used as filename
    """
    # Normalize timestamps (remove timezone)
    start = pd.Timestamp(start).tz_localize(None)
    end = pd.Timestamp(end).tz_localize(None)

    # Build a unique string
    key = f"{function_name}_{zone}_{start.strftime('%Y%m%d%H')}_{end.strftime('%Y%m%d%H')}"

    # Hash it to avoid long filenames and ensure filesystem safety
    return hashlib.md5(key.encode()).hexdigest()


def cache_load(function_name, start, end, zone):
    """
    Attempt to load cached data for a given function and time interval.

    Cache structure:
        cache/<function_name>/<hash>.pkl

    If the file exists:
        - print HIT log
        - return the unpickled object

    If the file does not exist:
        - print MISS log
        - return None
    """
    _ensure_dir(CACHE_DIR)
    subdir = os.path.join(CACHE_DIR, function_name)
    _ensure_dir(subdir)

    key = _make_cache_key(function_name, start, end, zone)
    path = os.path.join(subdir, f"{key}.pkl")

    # Cache HIT
    if os.path.exists(path):
        print(f"[CACHE] HIT {function_name} {zone} {start} → {end}")
        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception:
            # Corrupted cache file — ignore and regenerate
            print("[CACHE] ERROR reading cache file")
            return None

    # Cache MISS
    print(f"[CACHE] MISS {function_name} {zone} {start} → {end}")
    return None


def cache_save(function_name, start, end, zone, data):
    """
    Save data to cache.

    Parameters:
        function_name (str): category (prices, generation, dataset, etc.)
        start, end (Timestamp/str): time interval
        zone (str): bidding zone or country code
        data: any pickle-serializable object (usually a DataFrame)

    If saving fails (e.g. due to permissions), print an error but do not crash.
    """
    _ensure_dir(CACHE_DIR)
    subdir = os.path.join(CACHE_DIR, function_name)
    _ensure_dir(subdir)

    key = _make_cache_key(function_name, start, end, zone)
    path = os.path.join(subdir, f"{key}.pkl")

    try:
        with open(path, "wb") as f:
            pickle.dump(data, f)
        print(f"[CACHE] SAVED {function_name} {zone} {start} → {end}")
    except Exception:
        print("[CACHE] ERROR saving cache file")
