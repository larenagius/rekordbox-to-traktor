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

1. Bump `version` in `pyproject.toml`.
2. Run the one-command release script:

```powershell
Y:\Claude\GitHub\rb2traktor\scripts\release.ps1
```

It reads the version, runs the test suite (gate), builds the PyInstaller bundle on
**local disk** (building onto the NAS trips SMB file locks), zips it, and publishes
the app folder + zip to `Y:\Claude\releases\rb2traktor-<version>\`. Flags:

- `-Force` — overwrite an existing release of the same version.
- `-SkipTests` — skip the pytest gate (not recommended).
- `-Python <path>` / `-ReleasesRoot <path>` — override the build venv / output root.

All temp build dirs live under `%TEMP%` and are cleaned up automatically.

> **Why not build on the NAS:** PyInstaller can't clean its temp output on the
> SMB share (file locks). The script always builds locally and copies the result.

## Notes

- The live `collection.nml` is never modified by the app; output is always
  `collection-merge.nml`. See the safety notes in the README.
- Release artifacts are git-ignored — they are not committed to the repo, only
  published to `Y:\Claude\releases`.
