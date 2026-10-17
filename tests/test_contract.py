"""Source integrity contract: relative paths, byte sizes, content-sensitive hashes."""
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from input_manifest import manifest

with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp)
    (root/'nested').mkdir()
    (root/'nested'/'纹理.txt').write_text('shader',encoding='utf8')
    first=manifest(root)
    assert first['count']==1
    assert first['files'][0]['path']=='nested/纹理.txt'
    assert first['files'][0]['bytes']==6
    (root/'nested'/'纹理.txt').write_text('Shader',encoding='utf8')
    assert manifest(root)['files'][0]['sha256']!=first['files'][0]['sha256']
print('Manifest contract passed')
