import sys, collections
from trace import run
sc, arm, seed, cap = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
eng, log, events, done_at, snaps = run(sc, arm, seed, max_ticks=cap)
print("completions:", done_at[-6:], "final", len(eng.completed), "tick", eng.clock.tick)
last = done_at[-1][0]
for T in (last + 50, last + 600, cap - 1):
    if T >= len(log): continue
    print(f"\n--- tick {T} ---")
    for rid in sorted(snaps[T]):
        s = snaps[T][rid]; v = log[T].get(rid)
        print(rid, s['cell'], s['status'][:10], 'task', s['task'], s['phase'], 'goal', s['goal'], 'path', s['path'], '|', v[0], v[1][:70], 'cw', v[2], 'y', v[3])
print("\nverdict histogram after last completion:")
for rid in sorted(eng.robots):
    c = collections.Counter(log[t][rid][0] for t in range(last, len(log)) if rid in log[t])
    print(rid, dict(c))
print("\nevents after last completion:")
evs = [e for e in events if e['tick'] >= last]
print(collections.Counter(e['kind'] for e in evs))
for e in evs[:25]: print(e)
