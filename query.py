import sqlite3
import math

# ---------------- CONFIG ----------------
DB_PATH = "elevation.db"  # نام دیتابیسی که ساختی
LAT_USER = 35.715298  # مثلاً میدان آزادی تهران
LON_USER = 51.404343
FLIGHT_ALTITUDE_M = 150  # ارتفاع پرواز
RADIUS_KM = 1  # شعاع بررسی به کیلومتر
# ----------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # شعاع زمین به کیلومتر
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def query_obstacles_nearby(db_path, lat_user, lon_user, radius_km, flight_altitude_m):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    delta_deg = radius_km / 111.32  # تقریب تبدیل کیلومتر به درجه جغرافیایی

    cur.execute('''
        SELECT ed.lat, ed.lon, ed.elevation
        FROM elevation_index ei
        JOIN elevation_data ed ON ed.id = ei.id
        WHERE ei.minLat >= ? AND ei.maxLat <= ?
          AND ei.minLon >= ? AND ei.maxLon <= ?
    ''', (
        lat_user - delta_deg, lat_user + delta_deg,
        lon_user - delta_deg, lon_user + delta_deg
    ))

    count = 0
    for lat, lon, elev in cur.fetchall():
        distance = haversine(lat_user, lon_user, lat, lon)
        if distance <= radius_km and elev > flight_altitude_m:
            print(f"⚠️ مانع در lat={lat:.6f}, lon={lon:.6f}, elev={elev:.1f}m, dist={distance:.2f}km")
            count += 1

    if count == 0:
        print("✅ مانعی در شعاع مشخص شده یافت نشد.")

    conn.close()

if __name__ == "__main__":
    query_obstacles_nearby(DB_PATH, LAT_USER, LON_USER, RADIUS_KM, FLIGHT_ALTITUDE_M)
