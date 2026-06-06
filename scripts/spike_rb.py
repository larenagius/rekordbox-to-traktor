"""Read-only spike: introspect the real Rekordbox master.db via pyrekordbox.

Confirms the SQLCipher key works and discovers the exact attribute/field names we
need for the production reader (path, bpm, cues, beatgrid, playlists).

This NEVER writes to the database. Run:
    python scripts/spike_rb.py
"""

import sys
import traceback

from pyrekordbox import Rekordbox6Database


def show(obj, attrs):
    for a in attrs:
        try:
            print(f"    {a} = {getattr(obj, a)!r}")
        except Exception as e:  # noqa: BLE001
            print(f"    {a} = <err {e}>")


def main():
    db = Rekordbox6Database()
    print("DB opened OK")

    contents = list(db.get_content())
    print(f"content rows: {len(contents)}")
    c = contents[0]
    print("=== first content: column names ===")
    cols = [k for k in vars(c).keys() if not k.startswith("_")]
    print("   ", cols)
    print("=== first content: key attrs ===")
    show(c, ["ID", "Title", "BPM", "FolderPath", "FileNameL", "FileSize",
             "Length", "BitRate", "Commnt", "Rating"])
    # path helpers
    for meth in ("get_path", "FolderPath"):
        try:
            v = getattr(c, meth)
            v = v() if callable(v) else v
            print(f"    path via {meth}: {v!r}")
        except Exception as e:  # noqa: BLE001
            print(f"    path via {meth}: <err {e}>")

    # Artist relationship
    try:
        print("    Artist:", c.Artist.Name if c.Artist else None)
    except Exception as e:  # noqa: BLE001
        print("    Artist err:", e)

    # Cues
    print("=== cues ===")
    try:
        cues = db.get_cue(ContentID=c.ID).all()
        print(f"  cues for first track: {len(cues)}")
        if not cues:
            # find a track that has cues
            allc = db.get_cue().limit(2000).all()
            print(f"  total cue rows (sample up to 2000): {len(allc)}")
            if allc:
                cues = [allc[0]]
        if cues:
            cc = cues[0]
            ccols = [k for k in vars(cc).keys() if not k.startswith("_")]
            print("  cue columns:", ccols)
            show(cc, ["ContentID", "InMsec", "OutMsec", "Kind", "ColorTableID",
                      "ColorID", "Color", "Comment", "Rgb", "is_memory_cue",
                      "ActiveLoop", "OrderNo"])
    except Exception as e:  # noqa: BLE001
        print("  cue error:", e)
        traceback.print_exc()

    # Playlists
    print("=== playlists ===")
    try:
        pls = db.get_playlist().all()
        print(f"  playlist rows: {len(pls)}")
        if pls:
            p = pls[0]
            pcols = [k for k in vars(p).keys() if not k.startswith("_")]
            print("  playlist columns:", pcols)
            show(p, ["ID", "Name", "ParentID", "Attribute", "is_folder", "Seq"])
    except Exception as e:  # noqa: BLE001
        print("  playlist error:", e)

    # ANLZ / beatgrid
    print("=== anlz / beatgrid ===")
    try:
        anlz = db.get_anlz_dir(c.ID)
        print("  anlz dir:", anlz)
    except Exception as e:  # noqa: BLE001
        print("  get_anlz_dir err:", e)
    try:
        files = db.read_anlz_files(c.ID)
        print("  read_anlz_files keys:", list(files.keys()) if files else files)
        for path, anlz in (files or {}).items():
            try:
                bg = anlz.get("beat_grid")
                print(f"    {path}: beat_grid type {type(bg)} sample {str(bg)[:200]}")
            except Exception as e:  # noqa: BLE001
                print(f"    {path}: beat_grid err {e}")
            break
    except Exception as e:  # noqa: BLE001
        print("  read_anlz_files err:", e)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
