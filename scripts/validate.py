from pathlib import Path
import hashlib,json,subprocess,yaml
from jsonschema import Draft4Validator
from render import render,r,m

def objects(text): return [o for o in yaml.safe_load_all(text) if o]
def assert_contract(items):
    for o in items:
        kind=o['kind']; spec=o.get('spec',{})
        if kind=='HorizontalPodAutoscaler' and o.get('metadata',{}).get('name','scaling-demo')=='scaling-demo':
            assert 1 <= spec['minReplicas'] <= spec['maxReplicas'] <= 10
            assert spec['behavior']['scaleDown']['stabilizationWindowSeconds'] >= 300
        if kind=='VerticalPodAutoscaler':
            assert spec['updatePolicy']['updateMode']=='Off', 'Baseline must only recommend'
            assert spec['resourcePolicy']['containerPolicies'][0]['controlledValues']=='RequestsOnly'
        if kind=='ScaledObject':
            assert spec['maxReplicaCount']<=5 and spec['cooldownPeriod']>=300
        if kind=='NodePool':
            assert spec['limits']['cpu']=='32' and spec['disruption']['consolidationPolicy']=='WhenEmpty'
        if kind=='EC2NodeClass':
            assert spec['metadataOptions']['httpTokens']=='required'
        if kind=='APIService':
            assert not spec.get('insecureSkipTLSVerify',False), 'API aggregation TLS verification must stay enabled'
        if kind=='Deployment' and o['metadata']['name']=='scaling-demo':
            p=spec['template']['spec'];assert p['automountServiceAccountToken'] is False
            for c in p['containers']:
                assert '@sha256:' in c['image'] and c['resources']['requests']['cpu']
                assert c['securityContext']['allowPrivilegeEscalation'] is False

for source in m['sources']:
    assert hashlib.sha256((r/source['file']).read_bytes()).hexdigest()==source['sha256'],source['file']
if m['chart']:
    subprocess.run(['helm','lint','--strict',str(r/'vendor'/m['chart']),'-f',str(r/'values.yaml')],check=True)
text=render()
assert text==(r/'rendered/install.yaml').read_text(), 'Run make render after changing values'
installed=objects(text)
examples=[]
for p in sorted((r/'examples').glob('*.yaml')):
    if p.name!='prometheus-scrape.yaml': examples += objects(p.read_text())
all_objects=installed+examples
schema_objects=list(all_objects)
if (r/'vendor/cert-manager-crds.yaml').exists():schema_objects+=objects((r/'vendor/cert-manager-crds.yaml').read_text())
crd_schema=json.loads((r/'vendor/kubernetes-crd-openapi.json').read_text())
crd_schema['$ref']='#/components/schemas/io.k8s.apiextensions-apiserver.pkg.apis.apiextensions.v1.CustomResourceDefinition'
crd_validator=Draft4Validator(crd_schema)
custom={}
for o in schema_objects:
    if o['kind']=='CustomResourceDefinition':
        crd_validator.validate(o)
        for v in o['spec']['versions']:
            custom[(o['spec']['group']+'/'+v['name'],o['spec']['names']['kind'])]=v['schema']['openAPIV3Schema']
def schemas(items):
    standard=[]; count=0
    for o in items:
        if o['kind']=='CustomResourceDefinition': continue
        key=(o['apiVersion'],o['kind'])
        if key in custom:
            Draft4Validator(custom[key]).validate(o);count+=1
        else:standard.append(o)
    if standard:
        subprocess.run([str(r/'.tools/kubeconform'),'-strict','-summary','-kubernetes-version',m['kubernetesSchemaVersion']],input=yaml.safe_dump_all(standard),text=True,check=True)
    print('Custom resources validated against pinned upstream CRD schemas:',count)
schemas(all_objects)
assert_contract(all_objects)
if m['key']=='vpa':
    assert len([o for o in installed if o['kind']=='Deployment'])==1
    full=objects(render(['-f',str(r/'values-apply-resources.yaml')]))
    schemas(full)
    assert len([o for o in full if o['kind']=='Deployment'])==3
if m['key']=='metrics-server':
    assert '--kubelet-insecure-tls' not in text
if m['key']=='prometheus-adapter':
    assert 'demo_requests_per_second' in text
    assert not any(o['kind']=='APIService' and o['metadata']['name']=='v1beta1.external.metrics.k8s.io' for o in installed)
    scrape=yaml.safe_load((r/'examples/prometheus-scrape.yaml').read_text())
    assert {v.get('target_label') for v in scrape['scrape_configs'][0]['relabel_configs']} >= {'namespace','pod'}
# Mutation checks ensure a broken scaling guard or transport regression fails validation.
import copy
bad={'apiVersion':'autoscaling/v2','kind':'HorizontalPodAutoscaler','spec':{'minReplicas':1,'maxReplicas':100,'behavior':{'scaleDown':{'stabilizationWindowSeconds':300}}}}
for mutant in [bad,{'kind':'APIService','spec':{'insecureSkipTLSVerify':True}}]:
    try:assert_contract([mutant])
    except AssertionError:pass
    else:raise AssertionError('Unsafe mutation was not rejected')
print('PASS: source checksums, exact render, schemas and scaling guardrails; no deployment performed.')

# Demo source and mounted ConfigMap must remain the same application.
if (r/'demo/app.py').exists():
    cm=next(o for o in examples if o['kind']=='ConfigMap' and o['metadata']['name']=='scaling-demo-code')
    assert cm['data']['app.py']==(r/'demo/app.py').read_text()
# Pin every rendered controller/demo image, including opt-in VPA components.
def image_refs(value):
    refs=[]
    if isinstance(value,dict):
        for k,v in value.items():
            if k=='image' and isinstance(v,str):refs.append(v)
            else:refs+=image_refs(v)
    elif isinstance(value,list):
        for v in value:refs+=image_refs(v)
    return refs
refs=image_refs(all_objects)
if m['key']=='vpa':refs+=image_refs(full)
assert all('@sha256:' in i for i in refs), refs
assert sorted(set(refs))==json.loads((r/'images.lock.json').read_text())['images']
if m['key']=='knative':
    expected=(r/'rendered/kourier.yaml').read_text()
    assert expected in text
if (r/'scripts/configure.py').exists():
    import sys,tempfile
    with tempfile.TemporaryDirectory() as tmp:
        output=Path(tmp)/'site'
        args=[sys.executable,str(r/'scripts/configure.py'),'--cluster','staging-demo','--region','us-east-1','--controller-role-arn','arn:aws:iam::123456789012:role/StagingController','--output',str(output)]
        if m['key']=='karpenter':args+=['--node-role','StagingNodeRole','--ami','ami-0123456789abcdef0','--queue','staging-interruptions']
        subprocess.run(args,check=True)
        site_text=subprocess.check_output(['helm','template',m['release'],str(r/'vendor'/m['chart']),'--namespace',m['namespace'],'--include-crds','--api-versions','apiregistration.k8s.io/v1','-f',str(output/'values.yaml')],text=True)
        assert 'REPLACE_' not in site_text
        site_objects=objects(site_text)
        for name in ['nodepool.yaml','ec2nodeclass.yaml']:
            if (output/name).exists():site_objects+=objects((output/name).read_text())
        schemas(site_objects)
        # A second invocation must not overwrite reviewed private files.
        assert subprocess.run(args,capture_output=True).returncode!=0
        bad_args=[v.replace('123456789012','000000000000') for v in args]
        assert subprocess.run(bad_args,capture_output=True).returncode!=0
    print('PASS: private configuration renders, schema checks and overwrite/placeholder rejection.')
