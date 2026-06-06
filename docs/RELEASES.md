# Releases

Built releases live on the NAS:

```
Y:\Claude\releases\
  rb2traktor-<version>\          # the runnable app folder (rb2traktor.exe + _internal\)
  rb2traktor-<version>.zip       # zipped copy for distribution / backup
```

`<version>` matches `project.version` in `pyproject.toml` (currently `0.1.0`).

## Running a release

Open `Y:\Claude\releases\rb2traktor-<version>\` and double-click `rb2traktor.exe`.
Keep the whole folder together — the exe loads its `_internal\` siblings.

> **NAS cold-start note:** the app is ~170 MB of DLLs. If the NAS drive was
> asleep it may take a while to wake and load on first launch (and feel laggy).
> That's the drive spinning up, not the app hanging — give it a minute.

## Building a new release

**Always build on local disk, then copy to the NAS.** Building straight onto the
NAS share leaves PyInstaller unable to clean its temp output (SMB file locks).

```powershell
# 1. Build on C: (uses the local venv)
cd Y:\Claude\rb2traktor
C:\Users\laren\rb2traktor-venv\Scripts\pyinstaller.exe packaging\rb2traktor.spec `
  --distpath C:\Users\laren\rb2traktor-dist `
  --workpath C:\Users\laren\rb2traktor-build --noconfirm

# 2. Stage + zip locally, then copy the folder and zip into Y:\Claude\releases\rb2traktor-<version>\
#    (robocopy is best for the NAS copy: robocopy <src> <dest> /E /R:2 /W:5)
```

Bump `version` in `pyproject.toml` first so the release folder/zip are named for
the new version.

## Notes

- The live `collection.nml` is never modified by the app; output is always
  `collection-merge.nml`. See the safety notes in the README.
- Release artifacts are git-ignored — they are not committed to the repo, only
  published to `Y:\Claude\releases`.
