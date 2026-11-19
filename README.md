# tiny-chess-01

[![make.fun · tiny-chess-01](https://make.fun/badge/tiny-chess-01.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![rank](https://make.fun/badge/tiny-chess-01/nashirfauzan/tiny-chess-01/rank.svg)](https://make.fun/bounty/tiny-chess-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)
[![reward](https://make.fun/badge/tiny-chess-01/nashirfauzan/tiny-chess-01/reward.svg)](https://make.fun/bounty/tiny-chess-01?utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01)

A chess engine in 4,096 bytes of Python. `main.py` is the whole engine: an lzma payload plus the
unpacker that runs it, packed by the competition kit's own `makefun compress`. The payload is a
full engine:

- 0x88 board, copy-make moves, incremental material and piece-square evaluation, an incremental
  Zobrist hash, so a node costs two table lookups rather than a board scan.
- Transposition table, principal variation search, late move reductions, null-move pruning, killer
  moves and a history heuristic; quiescence that stands pat out of check and searches every evasion
  in check; repetition detection inside the search line.
- A deterministic node budget per move, derived from the game's move number, never from a clock:
  the same position always yields the same move, so a trial's replay reproduces every move and
  result.

It reads `MAKEFUN_ENV_URL`, asks the env for each game in turn, plays while it is its move, and exits
when every game is over. It makes no model call and imports nothing but the standard library.

`engine.py` is the readable source the entry is packed from.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=y7w5j81b&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
