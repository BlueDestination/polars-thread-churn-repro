"""Minimal repro: access violation in polars 2.x read_ipc.

The process's first `import polars` happens in a thread that then exits; afterwards
`pl.read_ipc` is called from short-lived threads. Crashes around round 150-200.

python repro.py [--rounds N] [--preload]
"""

import argparse
import faulthandler
import threading

BLOBS: list[bytes] = []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--rounds', type=int, default=1000)
    parser.add_argument('--preload', action='store_true', help='import polars on the main thread first (control run)')
    return parser.parse_args()


def seed() -> None:
    import polars as pl

    rows = 15000
    frame = pl.DataFrame({'i': range(rows), 'x': [i * 0.01 for i in range(rows)]})
    BLOBS.append(frame.write_ipc(file=None).getvalue())


def read_round() -> None:
    import polars as pl

    pl.read_ipc(BLOBS[0])


def main() -> int:
    faulthandler.enable()
    args = parse_args()
    if args.preload:
        import polars  # noqa: F401

    first = threading.Thread(target=seed, name='seed')
    first.start()
    first.join()

    for i in range(args.rounds):
        thread = threading.Thread(target=read_round, name='ScriptRunner.scriptThread')
        thread.start()
        thread.join()
        print(i, flush=True)

    print(f'no crash within {args.rounds} rounds', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
