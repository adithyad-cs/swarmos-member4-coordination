import json, collections, sys
rows = [json.loads(l) for l in open(sys.argv[1])]
def cat_term(t):
    r = t['reason'] or ''
    if t['d'] is not None and t['d'] < 0.75 and ('safety monitor' in r): return 'FLOOR_FREEZE(<0.75, kernel hold)'
    if 'safety monitor' in r or 'next step would come' in r or 'held' in r: return 'kernel/SAW hold (>=0.75)'
    if t['verdict'] == 'YIELD': return 'ladder YIELD'
    if t['verdict'] in ('PROCEED','SLOW'): return 'moving (' + t['verdict'] + ')'
    return t['verdict'] or 'none'
for key in sorted({(r['sc'], r['arm']) for r in rows}):
    g = [r for r in rows if (r['sc'], r['arm']) == key]
    dnf = [r for r in g if not r['finished']]
    print(f"\n=== {key[0]} / {key[1]}: {len(g)} runs, {len(dnf)} DNF")
    tc = collections.Counter(); peer_idle = collections.Counter(); floor_runs = 0; ends_floor_task = 0
    first_cause = collections.Counter(); onset_kinds = collections.Counter()
    for r in dnf:
        for t in r['terminal']:
            tc[cat_term(t)] += 1
            peer_idle['peer idle' if t['peer_idle'] else ('peer has task' if t['peer_idle'] is False else 'no peer')] += 1
        # pairs still inside floor at end involving a task-holding robot
        task_holders = {t['r'] for t in r['terminal']}
        fp = [p for p in r['inside_at_end'] if set(p) & task_holders]
        if fp: floor_runs += 1
        # first onset of the pair(s) that persist to the end
        persist = {tuple(p) for p in fp}
        ons = [o for o in r['onsets'] if tuple(o['pair']) in persist]
        if ons:
            o = ons[-1]   # the onset that started the final (unbroken) episode
            w = o['who']
            movers = [k for k, v in w.items() if v['moved'] > 0]
            corner = any(w[k]['corner'] for k in movers)
            vk = '+'.join(sorted(f"{w[k]['verdict']}" for k in movers)) or 'none moved'
            onset_kinds[f"corner={corner} movers={vk}"] += 1
            idle = ['idle' if w[k]['task'] is None else 'task' for k in w]
            first_cause['pair: ' + '/'.join(sorted(idle))] += 1
    print(" terminal verdicts of task holders:", dict(tc))
    print(" terminal blocker:", dict(peer_idle))
    print(f" DNF runs ending with a task-holder frozen inside 0.75 m: {floor_runs}/{len(dnf)}")
    print(" onset of that final floor episode:", dict(onset_kinds))
    print(" pair composition at onset:", dict(first_cause))
    fin = [r for r in g if r['finished']]
    if fin: print(" finished runs: margin breaches", [r['margin_breaches'] for r in fin])
    print(" DNF runs: margin breaches", sorted(r['margin_breaches'] for r in dnf))
