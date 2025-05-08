import rasterio
import sqlite3
import os
from rasterio.windows import from_bounds
from rasterio.transform import xy

# مسیر فایل GeoTIFF
tif_file = "elevation_data.tif"

# تنظیمات تایل مورد نظر (برای محدوده 37.9 تا 38.0 و 46.1 تا 46.2)
tile_lat = 37.9
tile_lon = 46.1
tile_size = 0.1
lat_min = tile_lat
lat_max = tile_lat + tile_size
lon_min = tile_lon
lon_max = tile_lon + tile_size

# مسیر خروجی دیتابیس
db_path = "tile_379_461_fixed.db"

# حذف دیتابیس قبلی اگر وجود دارد
if os.path.exists(db_path):
    os.remove(db_path)

with rasterio.open(tif_file) as src:
    nodata = src.nodata

    # تعیین پنجره‌ی مورد نظر
    window = from_bounds(lon_min, lat_min, lon_max, lat_max, src.transform)
    band = src.read(1, window=window)
    transform = src.window_transform(window)

    rows, cols = band.shape
    points = []

    for row in range(rows):
        for col in range(cols):
            elevation = band[row, col]
            if elevation == nodata:
                continue

            lon, lat = xy(transform, row, col, offset='center')  # ✅ استفاده از مرکز پیکسل
            points.append((lat, lon, float(elevation)))

# ساخت دیتابیس SQLite و ذخیره نقاط
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

print(f"✅ دیتابیس تایل ساخته شد: {db_path} (تعداد نقاط: {len(points)})")
