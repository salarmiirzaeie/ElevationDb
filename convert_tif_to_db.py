import rasterio
import sqlite3
import os
import math
from tqdm import tqdm
from rasterio.windows import Window

# -------------------- CONFIG --------------------
tif_file = "elevation_data.tif"
output_folder = "tiles"
tile_size = 0.1
min_points_per_tile = 1

# محدوده شمال‌غرب که باید رد بشه
exclude_min_lat, exclude_max_lat = 36.0, 39.5
exclude_min_lon, exclude_max_lon = 44.0, 48.5

# -------------------- SETUP ---------------------
os.makedirs(output_folder, exist_ok=True)

# -------------------- PROCESS -------------------
print("Reading GeoTIFF (excluding NW)...")
with rasterio.open(tif_file) as src:
    band = src.read(1)
    transform = src.transform
    nodata = src.nodata

    rows, cols = band.shape
    tile_map = {}

    print("Processing all pixels (excluding NW)...")
    for row in tqdm(range(rows)):
        for col in range(cols):
            elevation = band[row, col]
            if elevation == nodata:
                continue

            lon, lat = rasterio.transform.xy(transform, row, col)

            # رد کردن پیکسل‌هایی که در محدوده NW قرار دارند
            if (exclude_min_lat <= lat <= exclude_max_lat) and (exclude_min_lon <= lon <= exclude_max_lon):
                continue

            tile_lat = math.floor(lat / tile_size)
            tile_lon = math.floor(lon / tile_size)
            tile_key = f"{tile_lat}_{tile_lon}"

            if tile_key not in tile_map:
                tile_map[tile_key] = []

            tile_map[tile_key].append((lat, lon, float(elevation)))

# -------------------- WRITE TILES ---------------
print("Creating SQLite tiles (excluding NW)...")
for tile_key, points in tqdm(tile_map.items()):
    if len(points) < min_points_per_tile:
        continue

    db_path = os.path.join(output_folder, f"{tile_key}.db")

    # اگر قبلاً ساخته شده، رد کن
    if os.path.exists(db_path):
        continue

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS elevation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lat REAL,
            lon REAL,
            elevation REAL
        )
    ''')

    cur.executemany('''
        INSERT INTO elevation (lat, lon, elevation)
        VALUES (?, ?, ?)
    ''', points)

    conn.commit()
    conn.close()

print("✅ Done! All non-NW tiles added to 'tiles' folder.")
