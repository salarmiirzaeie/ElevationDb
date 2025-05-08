import rasterio

# مسیر فایل GeoTIFF
file_path = "elevation_data.tif"

with rasterio.open(file_path) as src:
    pixel_size = src.res  # (عرض پیکسل، ارتفاع پیکسل)
    width = src.width     # تعداد پیکسل در عرض
    height = src.height   # تعداد پیکسل در ارتفاع
    crs = src.crs         # سیستم مختصات
    bounds = src.bounds   # مختصات گوشه‌های فایل

    print(f"✅ Pixel size (resolution): {pixel_size[0]} x {pixel_size[1]} units")
    print(f"🖼 Dimensions: {width} x {height} pixels")
    print(f"🌍 CRS (Coordinate System): {crs}")
    print(f"📐 Bounds: {bounds}")
