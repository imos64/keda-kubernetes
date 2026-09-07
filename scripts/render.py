from pathlib import Path
import json,subprocess
r=Path(__file__).resolve().parents[1]
m=json.loads((r/'package.json').read_text())
def render(extra=()):
    if m['chart']:
        return subprocess.check_output(['helm','template',m['release'],str(r/'vendor'/m['chart']),'--namespace',m['namespace'],'--include-crds','--api-versions','apiregistration.k8s.io/v1','--kube-version',m['kubernetesSchemaVersion'],'-f',str(r/'values.yaml'),*extra],text=True)
    if m['key']=='knative':
        return '\n---\n'.join((r/'vendor'/f).read_text() for f in ['serving-crds.yaml','serving-core.yaml','kourier.yaml'])
    return '# HPA is built into Kubernetes. No controller installation manifest is needed.\n'
if __name__=='__main__':
    (r/'rendered').mkdir(exist_ok=True)
    (r/'rendered/install.yaml').write_text(render())
    print('Rendered files only; no cluster was accessed.')
