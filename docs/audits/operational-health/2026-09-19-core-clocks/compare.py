import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--base', required=True)
p.add_argument('--head', default='HEAD')
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()

def blob(ref, path):
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'])

def read(ref, path):
    return json.loads(blob(ref, path))

old = read(a.base, 'data/ipos.json')
new = read(a.head, 'data/ipos.json')
before = {row['id']: row for row in old['ipos']}
after = {row['id']: row for row in new['ipos']}
counts = Counter()
changed = []
non_clock = []
def changes(x, y, prefix=''):
    if x == y:
        return []
    if isinstance(x, dict) and isinstance(y, dict):
        out = []
        for key in sorted(x.keys() | y.keys()):
            path = f'{prefix}.{key}' if prefix else key
            if key not in x or key not in y:
                out.append(path)
            else:
                out.extend(changes(x[key], y[key], path))
        return out
    return [prefix]
for key in before.keys() & after.keys():
    paths = changes(before[key], after[key])
    if paths:
        changed.append(key)
        counts.update(paths)
        substantive = [path for path in paths if path not in ('staticSourcePolicy.checkedAt', 'validation.checkedAt')]
        if substantive:
            non_clock.append({'id': key, 'paths': substantive})
out = {'base': a.base, 'head': a.head, 'recordCountBefore': len(before), 'recordCountAfter': len(after),
       'added': sorted(after.keys() - before.keys()), 'removed': sorted(before.keys() - after.keys()),
       'changedRecordCount': len(changed), 'changedPaths': dict(counts.most_common()),
       'nonPolicyClockChanges': sorted(non_clock, key=lambda x:x['id']),
       'pendingBytesUnchanged': blob(a.base, 'data/pending_updates.json') == blob(a.head, 'data/pending_updates.json'),
       'phaseBefore': read(a.base, 'data/phase_status.json'), 'phaseAfter': read(a.head, 'data/phase_status.json'),
       'coreHealth': {key:new['meta']['sourceHealth'].get(key) for key in ('NSE-live','NSE-history','BSE','SEBI')},
       'publication': new['meta'].get('publication'),
       'sha256': {path:hashlib.sha256(blob(a.head,path)).hexdigest() for path in ('data/ipos.json','data/pending_updates.json','data/ipos-summary.json','data/phase_status.json')}}
a.output.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
print(json.dumps({key:out[key] for key in ('recordCountBefore','recordCountAfter','added','removed','changedRecordCount','pendingBytesUnchanged')}, indent=2))
