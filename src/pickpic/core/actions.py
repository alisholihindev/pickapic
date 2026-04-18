from __future__ import annotations

import os
import shutil
import sqlite3
from pathlib import Path

import send2trash

from pickpic.core import index as db


def delete(con: sqlite3.Connection, paths: list[str]) -> None:
    bid = db.next_batch_id(con)
    for p in paths:
        if not Path(p).exists():
            continue
        send2trash.send2trash(p)
        db.log_undo(con, bid, "delete", p)
        con.execute("DELETE FROM images WHERE path=?", (p,))
    con.commit()


def move(con: sqlite3.Connection, paths: list[str], dest_dir: str) -> None:
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    bid = db.next_batch_id(con)
    for p in paths:
        src = Path(p)
        if not src.exists():
            continue
        dst = dest / src.name
        # Avoid name collision
        counter = 1
        while dst.exists():
            dst = dest / f"{src.stem}_{counter}{src.suffix}"
            counter += 1
        shutil.move(str(src), str(dst))
        db.log_undo(con, bid, "move", str(src), str(dst))
        con.execute("UPDATE images SET path=? WHERE path=?", (str(dst), p))
    con.commit()


def rename(con: sqlite3.Connection, path: str, new_name: str) -> str:
    src = Path(path)
    if not src.exists():
        raise FileNotFoundError(path)
    dst = src.parent / new_name
    if dst.exists():
        raise FileExistsError(str(dst))
    os.rename(str(src), str(dst))
    bid = db.next_batch_id(con)
    db.log_undo(con, bid, "rename", str(src), str(dst))
    con.execute("UPDATE images SET path=? WHERE path=?", (str(dst), path))
    con.commit()
    return str(dst)


def undo_last(con: sqlite3.Connection) -> int:
    ops = db.pop_undo_batch(con)
    count = 0
    for op in ops:
        try:
            if op["op"] == "delete":
                # Items are in trash — we can't auto-restore, so just re-add path to DB
                # (user must manually restore from trash if needed)
                pass
            elif op["op"] == "move":
                dst = Path(op["dst"])
                src = Path(op["src"])
                if dst.exists():
                    src.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(dst), str(src))
                    con.execute("UPDATE images SET path=? WHERE path=?", (str(src), str(dst)))
                    count += 1
            elif op["op"] == "rename":
                dst = Path(op["dst"])
                src = Path(op["src"])
                if dst.exists():
                    os.rename(str(dst), str(src))
                    con.execute("UPDATE images SET path=? WHERE path=?", (str(src), str(dst)))
                    count += 1
        except OSError:
            pass
    con.commit()
    return count
