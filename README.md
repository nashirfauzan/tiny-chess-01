# tiny-chess-01 entry

A chess engine in 4,096 bytes of Python. `main.py` is an lzma payload plus its unpacker; the payload
is a full engine:

- 0x88 board, copy-make moves, incremental material + piece-square evaluation and an incremental
  Zobrist hash, so a node costs two table lookups rather than a board scan.
- Transposition table, principal variation search, late move reductions, null-move pruning, killer
  moves and a history heuristic, quiescence with delta-free capture search and full evasions in check,
  check extensions, and repetition detection inside the search line.
- A deterministic node budget per move derived from the game's move number: no wall clock and no
  unseeded randomness anywhere, so a replay of a trial reproduces every move and result.

It reads `MAKEFUN_ENV_URL`, asks the env for each game in turn, plays while it is its move, and exits
when every game is over. It makes no model call and imports nothing but the standard library.

Run it as the competition does:

    python3 -P -s main.py

MIT licensed.