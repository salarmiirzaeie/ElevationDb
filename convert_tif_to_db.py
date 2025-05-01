import rasterio
import sqlite3
import os
from tqdm import tqdm
import math

# --- CONFIG ---
tif_file = 'elevation_data.tif'
db_file = 'elevation.db'
sample_step = 2  # use every pixel (can increase for downsampling)
grid_size = 0.01  # اندازه گرید (تقریباً 1 کیلومتر)

def create_elevation_db(tif_file, db_file, sample_step=1, grid_size=0.01):
    if os.path.exists(db_file):
        os.remove(db_file)

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()

    # ایجاد جدول بهینه‌شده بدون id و با گرید
    cur.execute('''
        CREATE TABLE elevation_data (
            lat REAL,
            lon REAL,
            elevation REAL,
            grid_lat INTEGER,
            grid_lon INTEGER
        )
    ''')

    # ایجاد ایندکس برای پاسخ سریع به کوئری‌ها
    cur.execute('CREATE INDEX idx_grid ON elevation_data(grid_lat, grid_lon)')

    with rasterio.open(tif_file) as src:
        band = src.read(1)
        rows, cols = band.shape
        transform = src.transform

        batch_data = []
        batch_size = 10000  # برای کاهش دفعات commit

        for row in tqdm(range(0, rows, sample_step), desc="Processing"):
            for col in range(0, cols, sample_step):
                elevation = band[row, col]

                # نادیده گرفتن مقادیر نامعتبر (مثلاً nodata)
                if elevation == src.nodata:
                    continue

                lon, lat = rasterio.transform.xy(transform, row, col)

                # محاسبه grid index
                grid_lat = math.floor(lat / grid_size)
                grid_lon = math.floor(lon / grid_size)

                batch_data.append((lat, lon, float(elevation), grid_lat, grid_lon))

                if len(batch_data) >= batch_size:
                    cur.executemany('''
                        INSERT INTO elevation_data (lat, lon, elevation, grid_lat, grid_lon)
                        VALUES (?, ?, ?, ?, ?)
                    ''', batch_data)
                    conn.commit()
                    batch_data = []

        # وارد کردن باقی مانده‌ها
        if batch_data:
            cur.executemany('''
                INSERT INTO elevation_data (lat, lon, elevation, grid_lat, grid_lon)
                VALUES (?, ?, ?, ?, ?)
            ''', batch_data)
            conn.commit()

    conn.close()
    print(f"✅ Database created successfully: {db_file}")

if __name__ == "__main__":
    create_elevation_db(tif_file, db_file, sample_step, grid_size)
