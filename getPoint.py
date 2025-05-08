import rasterio
from rasterio.transform import rowcol

# مسیر فایل GeoTIFF
tif_path = "elevation_data.tif"

# مختصات نقطه مورد نظر (Longitude, Latitude)
longitude = 46.10565
latitude = 37.95028

# باز کردن فایل tif
with rasterio.open(tif_path) as src:
    # تبدیل مختصات جغرافیایی به مختصات رستر (سطر و ستون)
    row, col = rowcol(src.transform, longitude, latitude)

    # خواندن مقدار ارتفاع در پیکسل مربوطه
    elevation = src.read(1)[row, col]

    print(f"ارتفاع در نقطه ({latitude}, {longitude}) برابر است با: {elevation} متر")
