"""SWARMOS M4 - directional traffic rules on single-file segments.

What this is, stated without inflation: ONE-WAY LANES, an established
technique in AGV/AMR fleets and one of the classical MAPF families ("rule-based"
/ traffic-rule planners). It is NOT a new algorithm. It is here because it
removes, structurally, the failure our own measurements show dominates
single-file floors.

The measured problem it solves
------------------------------
On the overlap_batch floor (single-file aisles, single-file station rows) every
policy we have - textbook stop-and-wait, tuned stop-and-wait, and the SWARMOS
ladder - wedged head-on hundreds of times per run and finished only 3-35 of 60
tasks in 20 simulated minutes. Two robots meeting head-on in a one-cell-wide
corridor can never pass; a local rule can only hold one of them, and in a
chain of corridors the holds interlock. Warehouse.standard() says it plainly:
"ANY policy without joint multi-step planning gridlocks permanently".

The rule
--------
Each robot derives the SAME rule set from its onboard static map (racks only,
never the dynamic blockage), so there is nothing to negotiate and nothing to
transmit - the coordination is decentralized by construction:

  * a CORRIDOR cell is a navigable cell whose two lateral neighbours (across
    the axis of travel) are both impassable. Vertical corridor cells belong to
    a north-south aisle, horizontal ones to an east-west row;
  * vertical corridors alternate direction by column (northbound, southbound,
    northbound, ...), horizontal ones by row half (upper half eastbound, lower
    half westbound);
  * the 2-wide perimeter ring is a one-way loop, anticlockwise in screen terms:
    west side northbound, east side southbound. Moves ACROSS the ring (between
    its two lanes) are always allowed;
  * every other cell (junctions, two-way aisles, open floor) is unrestricted.

A move is forbidden only if it travels ALONG a restricted cell's axis against
that cell's direction, checked at both ends of the move. Because every aisle
direction has a partner running the other way and the ring closes the loop,
the directed graph stays strongly connected on the warehouse layouts this
project generates; strongly_connected() verifies that rather than assuming it,
and the planner falls back to the undirected route if a rule set ever strands a
robot (counted, never silent).

What it does NOT do: it does not touch the safety kernel, does not move any
robot, and does not change the baseline, which keeps plain shortest paths.
"""

from __future__ import annotations

from collections import deque
from typing import Optional

Cell = tuple[int, int]

# Direction vectors in grid coordinates. y grows southward (row 0 is the top /
# north wall where the drop stations are).
NORTH = (0, -1)
SOUTH = (0, 1)
EAST = (1, 0)
WEST = (-1, 0)


class TrafficRules:
    """One-way lane directions derived from a static warehouse map."""

    def __init__(self, warehouse) -> None:
        self.width = warehouse.width
        self.height = warehouse.height
        self._free = [
            [warehouse.cell_at(cx, cy) is not None
             and warehouse.cell_at(cx, cy).value != "RACK"
             for cx in range(self.width)]
            for cy in range(self.height)
        ]
        # cell -> required unit direction along its axis
        self.direction: dict[Cell, tuple[int, int]] = {}
        self.corridor_cells: set[Cell] = set()
        self._derive()

    # -- geometry ------------------------------------------------------------

    def _open(self, cx: int, cy: int) -> bool:
        return 0 <= cx < self.width and 0 <= cy < self.height and self._free[cy][cx]

    def _ring(self, cx: int) -> Optional[str]:
        if cx < 2:
            return "WEST"
        if cx >= self.width - 2:
            return "EAST"
        return None

    def _derive(self) -> None:
        # Vertical corridor columns, numbered left to right so directions
        # alternate between neighbouring aisles.
        vertical_cols: list[int] = []
        for cy in range(self.height):
            for cx in range(self.width):
                if not self._open(cx, cy) or self._ring(cx) is not None:
                    continue
                lat_blocked = not self._open(cx - 1, cy) and not self._open(cx + 1, cy)
                if lat_blocked and cx not in vertical_cols:
                    vertical_cols.append(cx)
        vertical_cols.sort()
        col_dir = {
            cx: (NORTH if i % 2 == 0 else SOUTH)
            for i, cx in enumerate(vertical_cols)
        }

        for cy in range(self.height):
            for cx in range(self.width):
                if not self._open(cx, cy):
                    continue
                ring = self._ring(cx)
                if ring is not None:
                    # One-way perimeter loop. Rows that are full cross aisles
                    # still get the ring rule on the ring columns.
                    self.direction[(cx, cy)] = NORTH if ring == "WEST" else SOUTH
                    continue
                vertical = not self._open(cx - 1, cy) and not self._open(cx + 1, cy)
                horizontal = not self._open(cx, cy - 1) and not self._open(cx, cy + 1)
                if vertical and not horizontal:
                    self.direction[(cx, cy)] = col_dir[cx]
                    self.corridor_cells.add((cx, cy))
                elif horizontal and not vertical:
                    self.direction[(cx, cy)] = (
                        EAST if cy < self.height // 2 else WEST
                    )
                    self.corridor_cells.add((cx, cy))
                # dead ends (both) and open cells (neither) stay unrestricted

    # -- the rule --------------------------------------------------------------

    def _cell_ok(self, cell: Cell, move: tuple[int, int]) -> bool:
        need = self.direction.get(cell)
        if need is None:
            return True
        along = (move[0] != 0) == (need[0] != 0)
        if not along:
            return True           # moving across the lane axis is not restricted
        return move == need

    def edge_allowed(self, a: Cell, b: Cell) -> bool:
        """Whether a single 4-connected move a -> b obeys the traffic rules."""
        move = (b[0] - a[0], b[1] - a[1])
        return self._cell_ok(a, move) and self._cell_ok(b, move)

    # -- verification ------------------------------------------------------------

    def strongly_connected(self) -> bool:
        """Every free cell can reach every other under the rules.

        Checked by a forward and a reverse BFS from one cell; both must cover
        every free cell. Cheap (O(cells)) and run once per map.
        """
        cells = [(cx, cy) for cy in range(self.height) for cx in range(self.width)
                 if self._open(cx, cy)]
        if not cells:
            return True
        root = cells[0]

        def reach(forward: bool) -> set[Cell]:
            seen = {root}
            queue = deque([root])
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (cx + dx, cy + dy)
                    if nxt in seen or not self._open(*nxt):
                        continue
                    ok = (self.edge_allowed((cx, cy), nxt) if forward
                          else self.edge_allowed(nxt, (cx, cy)))
                    if ok:
                        seen.add(nxt)
                        queue.append(nxt)
            return seen

        total = len(cells)
        return len(reach(True)) == total and len(reach(False)) == total

    def summary(self) -> dict:
        return {
            "restricted_cells": len(self.direction),
            "corridor_cells": len(self.corridor_cells),
            "strongly_connected": self.strongly_connected(),
        }
