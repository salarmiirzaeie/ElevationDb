import rasterio
import sqlite3
import os
import math
from rasterio.windows import from_bounds
from rasterio.transform import xy
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

# -------------------- CONFIG --------------------
tif_file = "elevation_data.tif"
output_folder = "tiles"
tile_size = 0.1
min_points_per_tile = 1

IRAN_MIN_LAT, IRAN_MAX_LAT = 24.0, 40.0
IRAN_MIN_LON, IRAN_MAX_LON = 44.0, 64.0

os.makedirs(output_folder, exist_ok=True)

def process_tile(args):
    tile_lat, tile_lon = args

    db_path = os.path.join(output_folder, f"{tile_lat}_{tile_lon}.db")
    if os.path.exists(db_path):
        return

    lat_min = tile_lat * tile_size
    lat_max = lat_min + tile_size
    lon_min = tile_lon * tile_size
    lon_max = lon_min + tile_size

    try:
        with rasterio.open(tif_file) as src:
            window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
            band = src.read(1, window=window)
            transform = src.window_transform(window)
            nodata = src.nodata

            rows, cols = band.shape
            points = []
            for row in range(rows):
                for col in range(cols):
                    elevation = band[row, col]
                    if elevation == nodata:
                        continue
                    lon, lat = xy(transform, row, col, offset='center')
                    points.append((lat, lon, float(elevation)))

            if len(points) < min_points_per_tile:
                return

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
    except Exception as e:
        print(f"⛔️ خطا در پردازش تایل {tile_lat}_{tile_lon}: {e}")

# -------------------- MAIN --------------------

if __name__ == "__main__":
    lat_tiles = list(range(math.floor(IRAN_MIN_LAT / tile_size), math.ceil(IRAN_MAX_LAT / tile_size)))
    lon_tiles = list(range(math.floor(IRAN_MIN_LON / tile_size), math.ceil(IRAN_MAX_LON / tile_size)))

    tile_coords = [(lat, lon) for lat in lat_tiles for lon in lon_tiles]

    print(f"🧵 شروع پردازش موازی {len(tile_coords)} تایل...")

    with ProcessPoolExecutor() as executor:
        list(tqdm(executor.map(process_tile, tile_coords), total=len(tile_coords)))
