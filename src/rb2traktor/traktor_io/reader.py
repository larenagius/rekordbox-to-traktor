"""Read a Traktor collection.nml into canonical models, using lxml directly.

Why lxml and not traktor-nml-utils: Traktor Pro 4's NML carries attributes the
Traktor-3-era helper library does not model -- notably ``COLOR`` on CUE_V2 and the
``<GRID BPM>`` child element for grid markers. Round-tripping through a partial
schema risks silently dropping those. Parsing the raw tree ourselves lets us read
exactly what's there and (in writer.py) write back byte-faithfully, touching only
the elements we intend to change.

The live collection.nml is opened **read-only**. We keep the parsed lxml tree on
the reader so the writer can mutate a *copy* of it and serialize to a merge file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from lxml import etree

from ..models import Cue, CueKind, TraktorEntry
from ..matcher import paths

# Traktor CUE_V2 TYPE values
TK_TYPE_CUE = 0
TK_TYPE_FADE_IN = 1
TK_TYPE_FADE_OUT = 2
TK_TYPE_LOAD = 3
TK_TYPE_GRID = 4
TK_TYPE_LOOP = 5


def _hex_to_rgb(s: Optional[str]) -> Optional[tuple[int, int, int]]:
    if not s:
        return None
    s = s.lstrip("#")
    if len(s) != 6:
        return None
    try:
        return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))
    except ValueError:
        return None


def _is_autogrid_load_cue(el: etree._Element) -> bool:
    """True for Traktor's auto-generated grid load marker.

    Traktor pairs every beatgrid with a TYPE=0 HOTCUE=0 cue named "AutoGrid" at
    the grid anchor. It is not a user cue, so we exclude it from the canonical cue
    set -- otherwise every track would look like a conflict just because Traktor
    auto-placed this marker.
    """
    return (
        int(el.get("TYPE", "0")) == TK_TYPE_CUE
        and (el.get("NAME", "") == "AutoGrid")
    )


def _cue_from_element(el: etree._Element) -> Optional[Cue]:
    """Convert a <CUE_V2> element to a canonical Cue, or None for non-user markers.

    Grid markers (TYPE=4) and the auto-generated AutoGrid load cue are not user
    cues. Loops (LEN>0) are parsed as CueKind.LOOP but out of scope for v1 writing.
    """
    ctype = int(el.get("TYPE", "0"))
    if ctype == TK_TYPE_GRID or _is_autogrid_load_cue(el):
        return None

    start = float(el.get("START", "0") or 0)
    length = float(el.get("LEN", "0") or 0)
    hotcue = int(el.get("HOTCUE", "-1"))
    name = el.get("NAME", "") or ""
    color = _hex_to_rgb(el.get("COLOR"))

    if length > 0:
        kind = CueKind.LOOP
    elif hotcue >= 0:
        kind = CueKind.HOT
    else:
        kind = CueKind.MEMORY

    return Cue(
        position_ms=start,
        kind=kind,
        hotcue_index=hotcue if hotcue >= 0 else None,
        length_ms=length if length > 0 else None,
        name=name,
        color_rgb=color,
    )


def _entry_to_model(entry_el: etree._Element) -> TraktorEntry:
    loc = entry_el.find("LOCATION")
    if loc is not None:
        file_path = paths.traktor_location_to_path(
            loc.get("VOLUME", ""), loc.get("DIR", ""), loc.get("FILE", "")
        )
    else:
        file_path = ""

    info = entry_el.find("INFO")
    duration_ms = None
    file_size = None
    if info is not None:
        pt = info.get("PLAYTIME_FLOAT")
        if pt:
            duration_ms = float(pt) * 1000.0
        fs = info.get("FILESIZE")
        if fs:
            # Traktor stores FILESIZE in KB. Normalize to bytes for matching.
            file_size = int(fs) * 1024

    tempo = entry_el.find("TEMPO")
    bpm = float(tempo.get("BPM")) if (tempo is not None and tempo.get("BPM")) else None

    cues: list[Cue] = []
    has_grid = False
    for cue_el in entry_el.findall("CUE_V2"):
        if int(cue_el.get("TYPE", "0")) == TK_TYPE_GRID:
            has_grid = True
            continue
        c = _cue_from_element(cue_el)
        if c is not None:
            cues.append(c)

    return TraktorEntry(
        file_path=file_path,
        title=entry_el.get("TITLE", "") or "",
        artist=entry_el.get("ARTIST", "") or "",
        bpm=bpm,
        duration_ms=duration_ms,
        file_size=file_size,
        cues=cues,
        has_beatgrid=has_grid,
        raw=entry_el,
    )


class TraktorCollection:
    """Parsed, read-only view of a Traktor collection.nml.

    Use :meth:`entries` for the canonical projection used by the matcher, and
    :attr:`tree` / :attr:`source_path` when constructing the writer.
    """

    def __init__(self, source_path: str | Path):
        self.source_path = Path(source_path)
        # huge_tree handles the very large AUDIO_ID base64 blobs without limits.
        parser = etree.XMLParser(remove_blank_text=False, huge_tree=True)
        self.tree: etree._ElementTree = etree.parse(str(self.source_path), parser)
        self._root = self.tree.getroot()

    def entry_elements(self) -> list[etree._Element]:
        col = self._root.find("COLLECTION")
        return col.findall("ENTRY") if col is not None else []

    def entries(self) -> list[TraktorEntry]:
        return [_entry_to_model(e) for e in self.entry_elements()]

    @classmethod
    def load(cls, source_path: str | Path) -> "TraktorCollection":
        return cls(source_path)
