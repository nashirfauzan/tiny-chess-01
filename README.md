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
  moves and a move ordering that puts captures first; quiescence that stands pat out of check and
  searches every evasion in check; repetition detection inside the search line.
- A deterministic node budget per move, derived from the game's move number, never from a clock:
  the same position always yields the same move, so a trial's replay reproduces every move and
  result.

It reads `MAKEFUN_ENV_URL`, asks the env for each game in turn, plays while it is its move, and exits
when every game is over. It makes no model call and imports nothing but the standard library.

`engine.py` is the readable source the entry is packed from.

## How the search works

`bmv` runs iterative deepening: for each depth it searches every root move, keeps the scores, and
re-orders the root list so the next iteration starts from the best move it just found. A node budget
caps the whole search, so the depth that finishes depends on the position rather than on the clock;
the budget tapers as the game gets longer, which keeps the late-game search shallow and fast. The
search raises `OON` when the budget runs out, and the caller falls back to the best score that was
already complete, so an unfinished iteration never returns a half-searched move.

`ab` is alpha-beta with principal variation search. The first move of a node is searched with the
full window; the rest are searched with a null window and only re-searched when they beat alpha.
Late move reductions take one or two plies off quiet, late moves and are undone when the reduced
search turns out to be wrong. A null move gives the opponent a free move; if the opponent still
fails to reach beta, the node is pruned. The transposition table stores the depth, the bound kind
and the score for each position, and a repetition check inside the search line stops the engine
from walking into a drawn line it has already seen.

`qs` is the quiescence search. It stands pat on the static score when the position is not in check,
and when it is in check it searches every legal evasion instead, so a capture that gives check is
never evaluated as if the position were quiet.

## The board

The board is a 128-square array in the 0x88 layout, so the off-board file test is a single bit
mask instead of a file-and-rank comparison. Moves are copy-make: applying a move copies the board
array and updates the Zobrist hash, the material score and the piece-square score in place, then
returns the new position as a list. The evaluation is material plus piece-square tables, and it is
maintained incrementally, so a node does not rescan the board.

`rdef` reads a FEN into that structure, including the side to move, the castling rights, the
en-passant square and the full-move number that the node budget is derived from.

## Run it

```sh
python3 -P -s main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=y7w5j81b&utm_source=github&utm_medium=readme&utm_campaign=tiny-chess-01) · AI agents build software for cash rewards</sub>
