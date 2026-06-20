# PyInstaller spec for the rb2traktor GUI.
# Build:  pyinstaller packaging/rb2traktor.spec
# Output: dist/rb2traktor/rb2traktor.exe  (one-folder; more reliable than one-file
#         for PySide6 + pyrekordbox's bundled SQLCipher binaries).

# pyrekordbox ships data (key cache helpers, sqlcipher) and uses dynamic imports;
# collect everything to be safe.
import os, sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

# Absolute path to our source tree. SPECPATH is the spec's own directory (packaging/).
# Relative pathex resolves against an unpredictable CWD, which previously left the
# rb2traktor package out of the bundle entirely -> ModuleNotFoundError at startup.
SRC = os.path.abspath(os.path.join(SPECPATH, "..", "src"))
if SRC not in sys.path:
    sys.path.insert(0, SRC)  # so collect_submodules("rb2traktor") can import it

datas, binaries, hiddenimports = [], [], []
for pkg in ("pyrekordbox",):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h
hiddenimports += collect_submodules("sqlalchemy")
# rb2traktor uses lazy/dynamic imports (readers, writer) PyInstaller's static
# analysis won't all see -- collect the whole package explicitly.
hiddenimports += collect_submodules("rb2traktor")

block_cipher = None

a = Analysis(
    # Entry is a launcher that imports the GUI *as a package* so app.py's relative
    # imports resolve. Pointing Analysis straight at app.py runs it as __main__
    # with no parent package -> "attempted relative import" crash.
    [os.path.join(SPECPATH, "launch_gui.py")],
    pathex=[SRC],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib"],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

import os as _os
_CONSOLE = _os.environ.get("RB2T_CONSOLE") == "1"
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="rb2traktor",
    console=_CONSOLE,       # GUI app: no console window (set RB2T_CONSOLE=1 to debug)
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    name="rb2traktor",
)

# On macOS, wrap the COLLECT output into a proper .app bundle (double-clickable,
# no console). On Windows/Linux this is skipped and the one-folder build stands.
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="rb2traktor.app",
        icon=None,
        bundle_identifier="com.larenagius.rb2traktor",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.1.0",
            "LSMinimumSystemVersion": "11.0",
        },
    )
