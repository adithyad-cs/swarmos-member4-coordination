"""Ground-truth deadlock audit (observation only).

Built by the simulation from the verdicts every policy already returns: a
robot held by a WAIT / YIELD / REROUTE verdict that names a blocker
(`yield_to`, else the first of `conflict_with`) contributes one wait-for edge
robot -> blocker. A cycle in that graph is a deadlock: every robot in it is
waiting, directly or transitively, on itself.

It is policy-agnostic on purpose (the baseline names its blocker too), so the
same number is comparable across arms. It is an AUDIT - it never acts, never
touches the RNG or the trace hash - and it is not a claim that the robots
detect deadlock themselves.

Reported per run:
  deadlocks_formed       cycles that appeared
  deadlock_ticks_total   robot-cycle-ticks spent deadlocked
  mean / max duration    ticks from a cycle appearing to it breaking
  unresolved             cycles still present at the end of the run
"""

from __future__ import annotations

HOLDING = {"WAIT", "YIELD", "REROUTE"}
# A cycle lasting at least this long (1 s) is reported as PERSISTENT. Shorter
# cycles are routine: two robots in a contest can point at each other for a
# tick or two while right of way settles, and counting those as deadlocks
# would make the headline number meaningless.
PERSISTENT_TICKS = 10


class DeadlockAudit:
    def __init__(self) -> None:
        self._active: dict[frozenset, int] = {}   # cycle members -> start tick
        self.formed = 0
        self.durations: list[int] = []
        self.ticks_in_deadlock = 0

    @staticmethod
    def _edges(verdicts: dict) -> dict[str, str]:
        out: dict[str, str] = {}
        for rid in sorted(verdicts):
            v = verdicts[rid]
            if v.kind.value not in HOLDING:
                continue
            target = v.yield_to or (v.conflict_with[0] if v.conflict_with else None)
            if target and target != rid:
                out[rid] = target
        return out

    @staticmethod
    def cycles(edges: dict[str, str]) -> list[frozenset]:
        """All cycles of a graph with at most one outgoing edge per node."""
        found: list[frozenset] = []
        state: dict[str, int] = {}          # 1 = on current walk, 2 = finished
        for start in sorted(edges):
            if state.get(start):
                continue
            walk: list[str] = []
            node = start
            while node in edges and not state.get(node):
                state[node] = 1
                walk.append(node)
                node = edges[node]
            if state.get(node) == 1:
                found.append(frozenset(walk[walk.index(node):]))
            for n in walk:
                state[n] = 2
        return found

    def observe(self, tick: int, verdicts: dict) -> None:
        now = set(self.cycles(self._edges(verdicts)))
        for cyc in sorted(now - set(self._active), key=sorted):
            self._active[cyc] = tick
            self.formed += 1
        for cyc in sorted(set(self._active) - now, key=sorted):
            self.durations.append(tick - self._active.pop(cyc))
        self.ticks_in_deadlock += len(now)

    def summary(self) -> dict:
        d = self.durations
        return {
            "deadlocks_formed": self.formed,
            "persistent_deadlocks": (sum(1 for x in d if x >= PERSISTENT_TICKS)
                                     + len(self._active)),
            "persistent_threshold_ticks": PERSISTENT_TICKS,
            "deadlock_cycle_ticks": self.ticks_in_deadlock,
            "mean_duration_ticks": round(sum(d) / len(d), 2) if d else None,
            "max_duration_ticks": max(d) if d else None,
            "unresolved": len(self._active),
        }
