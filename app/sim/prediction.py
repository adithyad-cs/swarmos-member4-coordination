"""Scoring predicted conflicts against what actually happened (observation only).

The lookahead layer (app/coordination/lookahead.py) predicts, per robot, that a
pair will come within PREDICT_THRESHOLD_M in k ticks. This module, owned by the
simulation because only it knows TRUE positions, scores those predictions:

  actual conflict   a pair ENTERS the threshold on true positions (episode
                    start; a pair that stays close is one event, not many)
  true positive     an actual conflict for a pair that had an open prediction
                    made at least 1 tick earlier whose predicted tick is no more
                    than TOLERANCE_TICKS before the actual one
  false negative    an actual conflict with no such prediction
  false positive    a prediction whose predicted tick passed by more than
                    TOLERANCE_TICKS without the conflict occurring
  lead time         actual tick minus the tick the prediction was FIRST made

Honesty rule, stated in the report: when a proactive action PREVENTS a
predicted conflict, the prediction is scored as a false positive. Precision and
recall are therefore meaningful only in observe-only runs; effectiveness is
measured separately by the ablation.

Never touches motion, the RNG or the trace hash.
"""

from __future__ import annotations

from typing import Optional

# Equal to swarm_policy.CONFLICT_M (asserted in tests): the band in which the
# ladder treats an encounter as a genuine conflict.
PREDICT_THRESHOLD_M = 0.97
TOLERANCE_TICKS = 3


class PredictionScorer:
    def __init__(self) -> None:
        # pair -> [first_tick, predicted_abs_tick]
        self._open: dict[tuple[str, str], list[int]] = {}
        self._inside: set[tuple[str, str]] = set()
        self.predictions = 0            # prediction episodes opened
        self.actual = 0
        self.tp = 0
        self.fp = 0
        self.fn = 0
        self.leads: list[int] = []
        # Conflict episodes that ENDED (the pair left the conflict band). Every
        # ended episode is resolved without contact unless INV-1 fired, which
        # the safety summary reports separately.
        self.resolved = 0
        self.horizon_sum = 0
        self.horizon_n = 0

    @staticmethod
    def _key(a: str, b: str) -> tuple[str, str]:
        return (a, b) if a < b else (b, a)

    def observe_predictions(self, tick: int, predictions) -> None:
        for pc, _risk in predictions:
            key = self._key(pc.robot, pc.peer)
            if key in self._inside:
                continue              # already in conflict: not a prediction
            self.horizon_sum += pc.horizon
            self.horizon_n += 1
            at = tick + pc.lead_ticks
            entry = self._open.get(key)
            if entry is None:
                self._open[key] = [tick, at]
                self.predictions += 1
            else:
                entry[1] = min(entry[1], at) if entry[1] >= tick else at

    def observe_actual(self, tick: int, inside_now: set) -> None:
        """`inside_now`: pairs whose TRUE separation is below the threshold."""
        for key in sorted(inside_now - self._inside):
            self.actual += 1
            entry = self._open.pop(key, None)
            if entry is not None and entry[0] < tick:
                self.tp += 1
                self.leads.append(tick - entry[0])
            else:
                self.fn += 1
        self.resolved += len(self._inside - inside_now)
        self._inside = set(inside_now)
        for key in sorted(self._open):
            if tick > self._open[key][1] + TOLERANCE_TICKS:
                del self._open[key]
                self.fp += 1

    def summary(self) -> dict:
        def ratio(a: int, b: int) -> Optional[float]:
            return round(a / b, 4) if b else None
        leads = sorted(self.leads)
        return {
            "threshold_m": PREDICT_THRESHOLD_M,
            "tolerance_ticks": TOLERANCE_TICKS,
            "prediction_episodes": self.predictions,
            "actual_conflicts": self.actual,
            "resolved_conflicts": self.resolved,
            "open_conflicts": len(self._inside),
            "true_positives": self.tp,
            "false_positives": self.fp,
            "false_negatives": self.fn,
            "precision": ratio(self.tp, self.tp + self.fp),
            "recall": ratio(self.tp, self.tp + self.fn),
            "mean_lead_ticks": (round(sum(leads) / len(leads), 2) if leads else None),
            "median_lead_ticks": (leads[len(leads) // 2] if leads else None),
            "avg_horizon_ticks": (round(self.horizon_sum / self.horizon_n, 2)
                                  if self.horizon_n else None),
        }
