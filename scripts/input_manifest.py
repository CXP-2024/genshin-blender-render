"""Record source integrity; hashes do not prove material compatibility."""
import argparse
import hashlib
import json
from pathlib import Path

def manifest(root):
    root = Path(root).resolve(strict=True)
    files = [root] if root.is_file() else sorted(p for p in root.rglob('*') if p.is_file())
    records = []
    for p in files:
        h = hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda: f.read(1024*1024), b''):
                h.update(block)
        records.append({'path': p.name if root.is_file() else p.relative_to(root).as_posix(),
                        'bytes': p.stat().st_size, 'sha256': h.hexdigest()})
    return {'files':records, 'count':len(records)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if output.exists():
        raise SystemExit('Refusing to overwrite an existing manifest')
    data = manifest(args.root)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
