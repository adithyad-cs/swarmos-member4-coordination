import sys, math
from trace import run
sc, arm, seed, cap, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6]
eng, log, events, done_at, snaps = run(sc, arm, seed, max_ticks=cap)
def d(t):
    p, q = snaps[t][a]['xy'], snaps[t][b]['xy']; return math.hypot(p[0]-q[0], p[1]-q[1])
first = next(t for t in sorted(snaps) if d(t) < 0.75)
print("first tick below 0.75 m:", first, "dist", round(d(first),3))
for t in range(first-12, first+4):
    print(t, round(d(t),3), a, snaps[t][a]['xy'], snaps[t][a]['phase'], log[t][a][0], log[t][a][1][:60], log[t][a][4], '|', b, snaps[t][b]['xy'], snaps[t][b]['phase'], log[t][b][0], log[t][b][1][:60], log[t][b][4])
print("never back above 0.75 after?", all(d(t) < 0.76 for t in range(first, cap-1)))
