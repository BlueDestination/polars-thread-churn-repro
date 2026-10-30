# polars: access violation in `read_ipc` after thread churn

Minimal reproduction for <https://github.com/pola-rs/polars/issues/30362>.

`repro.py` does two things:

1. a thread performs the process's **first** `import polars`, writes a small IPC blob,
   and then exits;
2. afterwards, 1000 rounds of: spawn a fresh thread, `pl.read_ipc(blob)`, join.

On Windows this dies with an access violation around round 150-200:

```
Windows fatal exception: access violation

Current thread [ScriptRunner.scriptThread] (most recent call first):
  File "...\polars\io\ipc\functions.py", line 482 in scan_ipc
  File "...\polars\_utils\expired.py", line 114 in wrapper
  File "...\polars\io\ipc\functions.py", line 188 in read_ipc
```

Adding `--preload` (i.e. `import polars` on the main thread before any other thread
exists) makes the crash disappear, which points at thread-affine initialisation in
`_polars_runtime` being tied to the first importing thread.

## Observed results (GitHub-hosted runners, CPython 3.13)

| job | what it shows | observed |
| --- | --- | --- |
| `repro` (windows-latest) | first import in a dying thread + reads from fresh threads | access violation, exit 139, crash at round ~231 |
| `repro` (ubuntu-latest, macos-latest) | same script, same polars | 3000 rounds, no crash |
| `control` (all platforms) | same script with `--preload` | no crash |
| `versions` (windows-latest) | `1.44.2`, `2.0.0`, `2.1.0` | all three crash |

The crashing round depends on the machine (196 on a local Windows 11 box, 231 on CI), so the script
runs up to 3000 rounds by default.

Re-run everything with the **Re-run all jobs** button on any workflow run, or run locally:

```bash
uv run --python 3.13 --with polars==2.1.0 python repro.py --rounds 1000
uv run --python 3.13 --with polars==2.1.0 python repro.py --preload --rounds 1000
```

No streamlit, no sqlite, no data files: only `polars` and the standard library.
