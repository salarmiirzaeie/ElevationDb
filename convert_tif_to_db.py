import rasterio
import sqlite3
import os
import math
from tqdm import tqdm
from rasterio.windows import from_bounds

# -------------------- CONFIG --------------------
tif_file = "elevation_data.tif"  # مسیر فایل GeoTIFF اصلی
output_folder = "tiles"          # پوشه خروجی دیتابیس‌های tile
tile_size = 0.1                  # اندازه هر tile بر حسب درجه (مثلاً 0.1 درجه ≈ 11km)
min_points_per_tile = 1          # حداقل تعداد نقطه برای ایجاد یک tile

# فقط محدوده شمال غرب کشور
min_lat, max_lat = 36.0, 39.5
min_lon, max_lon = 44.0, 48.5

# -------------------- SETUP ---------------------
os.makedirs(output_folder, exist_ok=True)

# -------------------- PROCESS -------------------
print("Reading GeoTIFF (Northwest only)...")
with rasterio.open(tif_file) as src:
    # محاسبه window فقط برای شمال غرب
    window = from_bounds(min_lon, min_lat, max_lon, max_lat, transform=src.transform)
    band = src.read(1, window=window)
    transform = src.window_transform(window)
    nodata = src.nodata

    rows, cols = band.shape
    tile_map = {}

    print("Processing pixels in NW Iran...")
    for row in tqdm(range(rows)):
        for col in range(cols):
            elevation = band[row, col]
            if elevation == nodata:
                continue

            lon, lat = rasterio.transform.xy(transform, row, col)
            tile_lat = math.floor(lat / tile_size)
            tile_lon = math.floor(lon / tile_size)
            tile_key = f"{tile_lat}_{tile_lon}"

            if tile_key not in tile_map:
                tile_map[tile_key] = []

            tile_map[tile_key].append((lat, lon, float(elevation)))

# -------------------- WRITE TILES ---------------
print("Creating SQLite tiles...")
for tile_key, points in tqdm(tile_map.items()):
    if len(points) < min_points_per_tile:
        continue

    db_path = os.path.join(output_folder, f"{tile_key}.db")
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

print(f"✅ Done! Only northwest tiles are saved in '{output_folder}' folder.")
