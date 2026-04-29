from pathlib import Path

import imagehash
from PIL import Image, UnidentifiedImageError

GPS_INFO_TAG = 0x8825
GPS_LAT_REF_TAG = 1
GPS_LAT_TAG = 2
GPS_LON_REF_TAG = 3
GPS_LON_TAG = 4
GPS_IMG_DIRECTION_REF_TAG = 16
GPS_IMG_DIRECTION_TAG = 17
NORTH_TOLERANCE_DEGREES = 15.0


def _is_present(value) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple)):
        return len(value) > 0 and all(v is not None for v in value)
    return True


def _has_exif_gps(img: Image.Image) -> bool:
    gps_info = _get_gps_info(img)
    if not gps_info:
        return False
    return all(
        _is_present(gps_info.get(tag))
        for tag in (GPS_LAT_REF_TAG, GPS_LAT_TAG, GPS_LON_REF_TAG, GPS_LON_TAG)
    )


def _get_gps_info(img: Image.Image):
    try:
        exif = img.getexif()
    except Exception:
        return False
    if not exif:
        return None

    try:
        gps_info = exif.get_ifd(GPS_INFO_TAG)
    except Exception:
        gps_info = exif.get(GPS_INFO_TAG)
    if not gps_info:
        return False
    if not hasattr(gps_info, "get"):
        return None
    return gps_info


def _to_float(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_degrees(value) -> float | None:
    if not isinstance(value, (list, tuple)) or len(value) < 3:
        return None
    degrees = _to_float(value[0])
    minutes = _to_float(value[1])
    seconds = _to_float(value[2])
    if degrees is None or minutes is None or seconds is None:
        return None
    return degrees + (minutes / 60.0) + (seconds / 3600.0)


def _extract_coordinates(img: Image.Image) -> tuple[float | None, float | None]:
    gps_info = _get_gps_info(img)
    if not gps_info:
        return None, None

    lat = _to_degrees(gps_info.get(GPS_LAT_TAG))
    lon = _to_degrees(gps_info.get(GPS_LON_TAG))
    lat_ref = gps_info.get(GPS_LAT_REF_TAG)
    lon_ref = gps_info.get(GPS_LON_REF_TAG)
    if lat is None or lon is None or lat_ref is None or lon_ref is None:
        return None, None

    lat_ref = str(lat_ref).strip().upper()[:1]
    lon_ref = str(lon_ref).strip().upper()[:1]
    if lat_ref == "S":
        lat = -lat
    elif lat_ref != "N":
        return None, None

    if lon_ref == "W":
        lon = -lon
    elif lon_ref != "E":
        return None, None

    return round(lat, 6), round(lon, 6)


def _extract_heading(img: Image.Image) -> tuple[float | None, str | None, bool | None]:
    gps_info = _get_gps_info(img)
    if not gps_info:
        return None, None, None

    heading_ref = gps_info.get(GPS_IMG_DIRECTION_REF_TAG)
    heading = _to_float(gps_info.get(GPS_IMG_DIRECTION_TAG))
    if heading_ref is None or heading is None:
        return None, None, None

    heading_ref = str(heading_ref).strip().upper()[:1] or None
    heading = heading % 360.0
    delta = min(heading, 360.0 - heading)
    return heading, heading_ref, delta <= NORTH_TOLERANCE_DEGREES


def compute_hashes(path: str, extract_gps: bool = True) -> dict | None:
    """Return image hashes and extracted metadata or None on error."""
    try:
        with Image.open(path) as img:
            img.load()
            w, h = img.size
            ph = str(imagehash.phash(img))
            dh = str(imagehash.dhash(img))
            if extract_gps:
                has_gps = _has_exif_gps(img)
                gps_lat, gps_lon = _extract_coordinates(img)
                gps_heading, gps_heading_ref, is_facing_north = _extract_heading(img)
            else:
                has_gps = False
                gps_lat = gps_lon = None
                gps_heading = None
                gps_heading_ref = None
                is_facing_north = None
        return {
            "phash": ph,
            "dhash": dh,
            "width": w,
            "height": h,
            "has_gps": has_gps,
            "gps_lat": gps_lat,
            "gps_lon": gps_lon,
            "gps_heading": gps_heading,
            "gps_heading_ref": gps_heading_ref,
            "is_facing_north": is_facing_north,
        }
    except (UnidentifiedImageError, OSError, Exception):
        return None


def hamming(a: str, b: str) -> int:
    ha = imagehash.hex_to_hash(a)
    hb = imagehash.hex_to_hash(b)
    return ha - hb
