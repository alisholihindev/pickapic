import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from pickpic.config import DB_PATH

SCAN_METADATA_VERSION = 3


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS images (
                id         INTEGER PRIMARY KEY,
                path       TEXT UNIQUE NOT NULL,
                mtime      REAL NOT NULL,
                size       INTEGER NOT NULL,
                width      INTEGER,
                height     INTEGER,
                phash      TEXT,
                dhash      TEXT,
                has_gps    INTEGER,
                gps_lat    REAL,
                gps_lon    REAL,
                gps_heading REAL,
                gps_heading_ref TEXT,
                is_facing_north INTEGER,
                metadata_version INTEGER,
                blur_score REAL,
                is_blurry  INTEGER DEFAULT 0,
                scanned_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_images_path ON images(path);

            CREATE TABLE IF NOT EXISTS dup_groups (
                id         INTEGER PRIMARY KEY,
                group_type TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS group_members (
                group_id   INTEGER REFERENCES dup_groups(id) ON DELETE CASCADE,
                image_id   INTEGER REFERENCES images(id) ON DELETE CASCADE,
                score      REAL,
                is_kept    INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_gm_group ON group_members(group_id);
            CREATE INDEX IF NOT EXISTS idx_gm_image ON group_members(image_id);

            CREATE TABLE IF NOT EXISTS undo_log (
                id       INTEGER PRIMARY KEY,
                batch_id INTEGER NOT NULL,
                op       TEXT NOT NULL,
                src      TEXT NOT NULL,
                dst      TEXT,
                done_at  REAL
            );
            CREATE INDEX IF NOT EXISTS idx_undo_batch ON undo_log(batch_id);
        """)
        cols = {row["name"] for row in con.execute("PRAGMA table_info(images)").fetchall()}
        if "has_gps" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN has_gps INTEGER")
        if "gps_heading" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN gps_heading REAL")
        if "gps_heading_ref" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN gps_heading_ref TEXT")
        if "gps_lat" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN gps_lat REAL")
        if "gps_lon" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN gps_lon REAL")
        if "is_facing_north" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN is_facing_north INTEGER")
        if "metadata_version" not in cols:
            con.execute("ALTER TABLE images ADD COLUMN metadata_version INTEGER")


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()


def get_conn():
    """Return a persistent connection (caller must close)."""
    con = sqlite3.connect(DB_PATH, check_same_thread=False)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.row_factory = sqlite3.Row
    return con


def is_cached(con, path: str, mtime: float, size: int) -> bool:
    row = con.execute(
        """SELECT 1 FROM images
           WHERE path=? AND mtime=? AND size=? AND phash IS NOT NULL
             AND COALESCE(metadata_version, 0) >= ?""",
        (path, mtime, size, SCAN_METADATA_VERSION),
    ).fetchone()
    return row is not None


def upsert_image(
    con,
    *,
    path,
    mtime,
    size,
    width,
    height,
    phash,
    dhash,
    has_gps,
    gps_lat,
    gps_lon,
    gps_heading,
    gps_heading_ref,
    is_facing_north,
    blur_score,
    is_blurry,
):
    con.execute(
        """INSERT INTO images (
               path, mtime, size, width, height, phash, dhash, has_gps, gps_lat, gps_lon,
               gps_heading, gps_heading_ref, is_facing_north, metadata_version,
               blur_score, is_blurry, scanned_at
           )
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(path) DO UPDATE SET
               mtime=excluded.mtime, size=excluded.size,
               width=excluded.width, height=excluded.height,
               phash=excluded.phash, dhash=excluded.dhash, has_gps=excluded.has_gps,
               gps_lat=excluded.gps_lat, gps_lon=excluded.gps_lon,
               gps_heading=excluded.gps_heading, gps_heading_ref=excluded.gps_heading_ref,
               is_facing_north=excluded.is_facing_north, metadata_version=excluded.metadata_version,
               blur_score=excluded.blur_score, is_blurry=excluded.is_blurry,
               scanned_at=excluded.scanned_at""",
        (
            path, mtime, size, width, height, phash, dhash, int(has_gps), gps_lat, gps_lon,
            gps_heading, gps_heading_ref,
            None if is_facing_north is None else int(is_facing_north),
            SCAN_METADATA_VERSION,
            blur_score, int(is_blurry), time.time(),
        ),
    )


def get_all_hashes(con) -> list[dict]:
    rows = con.execute("SELECT id, path, phash, dhash FROM images WHERE phash IS NOT NULL").fetchall()
    return [dict(r) for r in rows]


def get_blurry_images(con) -> list[dict]:
    rows = con.execute(
        """SELECT id, path, blur_score, size, width, height, has_gps, gps_lat, gps_lon,
                  gps_heading, gps_heading_ref, is_facing_north
           FROM images WHERE is_blurry=1 ORDER BY blur_score ASC"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_images_without_geotag(con) -> list[dict]:
    rows = con.execute(
        """SELECT id, path, blur_score, size, width, height, has_gps, gps_lat, gps_lon,
                  gps_heading, gps_heading_ref, is_facing_north
           FROM images
           WHERE has_gps=0
           ORDER BY path COLLATE NOCASE"""
    ).fetchall()
    return [dict(r) for r in rows]


def get_images_not_facing_north(con) -> list[dict]:
    rows = con.execute(
        """SELECT id, path, blur_score, size, width, height, has_gps, gps_lat, gps_lon,
                  gps_heading, gps_heading_ref, is_facing_north
           FROM images
           WHERE has_gps=1 AND is_facing_north=0
           ORDER BY gps_heading ASC, path COLLATE NOCASE"""
    ).fetchall()
    return [dict(r) for r in rows]


def clear_groups(con) -> None:
    con.execute("DELETE FROM group_members")
    con.execute("DELETE FROM dup_groups")


def find_duplicate_geotag_groups(con) -> list[list[int]]:
    rows = con.execute(
        """SELECT gps_lat, gps_lon, GROUP_CONCAT(id) AS ids, COUNT(*) AS image_count,
                  COUNT(DISTINCT COALESCE(phash, '') || ':' || COALESCE(dhash, '')) AS hash_count
           FROM images
           WHERE has_gps=1 AND gps_lat IS NOT NULL AND gps_lon IS NOT NULL
           GROUP BY gps_lat, gps_lon
           HAVING image_count > 1 AND hash_count > 1
           ORDER BY image_count DESC, gps_lat ASC, gps_lon ASC"""
    ).fetchall()
    groups: list[list[int]] = []
    for row in rows:
        ids = [int(v) for v in str(row["ids"]).split(",") if v]
        if len(ids) > 1:
            groups.append(ids)
    return groups


def reset_db(con) -> None:
    """Delete all scanned data and groups, keeping schema intact."""
    con.execute("DELETE FROM undo_log")
    con.execute("DELETE FROM group_members")
    con.execute("DELETE FROM dup_groups")
    con.execute("DELETE FROM images")
    con.commit()


def insert_group(con, group_type: str, members: list[dict]) -> int:
    """members: list of {image_id, score}. Returns group id."""
    cur = con.execute("INSERT INTO dup_groups (group_type) VALUES (?)", (group_type,))
    gid = cur.lastrowid
    con.executemany(
        "INSERT INTO group_members (group_id, image_id, score) VALUES (?,?,?)",
        [(gid, int(m["image_id"]), float(m["score"])) for m in members],
    )
    return gid


def get_groups_page(con, group_type: str, offset: int, limit: int) -> list[dict]:
    rows = con.execute(
        "SELECT id FROM dup_groups WHERE group_type=? LIMIT ? OFFSET ?",
        (group_type, limit, offset),
    ).fetchall()
    groups = []
    for row in rows:
        members = con.execute(
            """SELECT i.id, i.path, i.width, i.height, i.size, i.blur_score, i.has_gps,
                      i.gps_lat, i.gps_lon, i.gps_heading, i.gps_heading_ref, i.is_facing_north,
                      gm.score, gm.is_kept
               FROM group_members gm JOIN images i ON i.id=gm.image_id
               WHERE gm.group_id=?""",
            (row["id"],),
        ).fetchall()
        groups.append({"id": row["id"], "members": [dict(m) for m in members]})
    return groups


def count_groups(con, group_type: str) -> int:
    return con.execute(
        "SELECT COUNT(*) FROM dup_groups WHERE group_type=?", (group_type,)
    ).fetchone()[0]


def count_blurry(con) -> int:
    return con.execute("SELECT COUNT(*) FROM images WHERE is_blurry=1").fetchone()[0]


def count_without_geotag(con) -> int:
    return con.execute("SELECT COUNT(*) FROM images WHERE has_gps=0").fetchone()[0]


def count_not_facing_north(con) -> int:
    return con.execute(
        "SELECT COUNT(*) FROM images WHERE has_gps=1 AND is_facing_north=0"
    ).fetchone()[0]


def count_scanned(con) -> int:
    return con.execute("SELECT COUNT(*) FROM images").fetchone()[0]


def next_batch_id(con) -> int:
    row = con.execute("SELECT MAX(batch_id) FROM undo_log").fetchone()
    return (row[0] or 0) + 1


def log_undo(con, batch_id: int, op: str, src: str, dst: str | None = None) -> None:
    con.execute(
        "INSERT INTO undo_log (batch_id, op, src, dst, done_at) VALUES (?,?,?,?,?)",
        (batch_id, op, src, dst, time.time()),
    )


def pop_undo_batch(con) -> list[dict]:
    row = con.execute("SELECT MAX(batch_id) FROM undo_log").fetchone()
    if row[0] is None:
        return []
    bid = row[0]
    rows = con.execute(
        "SELECT * FROM undo_log WHERE batch_id=? ORDER BY id DESC", (bid,)
    ).fetchall()
    con.execute("DELETE FROM undo_log WHERE batch_id=?", (bid,))
    return [dict(r) for r in rows]
