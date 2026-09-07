from pathlib import Path
import hashlib,io,tarfile,urllib.request
root=Path(__file__).resolve().parents[1]
tool=root/'.tools/kubeconform'
if not tool.exists():
    url='https://github.com/yannh/kubeconform/releases/download/v0.8.0/kubeconform-linux-amd64.tar.gz'
    blob=urllib.request.urlopen(url,timeout=60).read()
    assert hashlib.sha256(blob).hexdigest()=='9bc2bffbf71f261128533edaf912153948b7ff238f9a531ae6d34466ec287883'
    with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as archive:
        binary=archive.extractfile('kubeconform').read()
    tool.parent.mkdir(parents=True,exist_ok=True);tool.write_bytes(binary);tool.chmod(0o755)
