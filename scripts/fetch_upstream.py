from pathlib import Path
import json, urllib.request, hashlib, concurrent.futures, time
ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'source_manifest.json').read_text())
dest = Path('E:/Codex/downloads/openhand-hardware') / manifest['commit']
def fetch(item):
    p = dest / item['path']
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        url = 'https://raw.githubusercontent.com/grablab/openhand-hardware/' + manifest['commit'] + '/' + urllib.parse.quote(item['path'])
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=90) as r: data = r.read()
                p.write_bytes(data)
                break
            except Exception:
                if attempt == 2: raise
                time.sleep(1)
    data = p.read_bytes()
    gitsha = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    assert gitsha == item['sha'], item['path']
    return {'path': item['path'], 'size':len(data), 'sha256':hashlib.sha256(data).hexdigest(), 'git_blob_sha1':gitsha}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    records = list(pool.map(fetch, manifest['files']))
(ROOT/'upstream_checksums.json').write_text(json.dumps({'commit':manifest['commit'],'files':records},indent=2))
print(json.dumps({'directory':str(dest),'verified_files':len(records),'bytes':sum(r['size'] for r in records)}))
