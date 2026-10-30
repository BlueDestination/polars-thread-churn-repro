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

## Expected results

| job | what it shows | expected |
| --- | --- | --- |
| `repro` (windows-latest) | first import in a dying thread + reads from fresh threads | crash |
| `repro` (ubuntu-latest, macos-latest) | same script on other platforms | see logs |
| `control` (all platforms) | same script with `--preload` | no crash |
| `versions` (windows-latest) | `1.44.2`, `2.0.0`, `2.1.0` | see logs |

Re-run everything with the **Re-run all jobs** button on any workflow run, or run locally:

```bash
uv run --python 3.13 --with polars==2.1.0 python repro.py --rounds 1000
uv run --python 3.13 --with polars==2.1.0 python repro.py --preload --rounds 1000
```

No streamlit, no sqlite, no data files: only `polars` and the standard library.
