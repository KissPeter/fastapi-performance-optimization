import json
import yaml
from copy import deepcopy


# define a custom representer for strings
def quoted_presenter(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')


yaml.add_representer(str, quoted_presenter)

compos = yaml.load(open('../docker-compose.yml'), Loader=yaml.Loader)
compose_out = {"version": "3.1", "services": {}}
print(f" Using {compos['services']['app_w3_t2']} as sample")
sample = compos['services']['app_w3_t2']
# {'image': 'fastapi-performance-optimization:latest', 'cpus': 2, 'ports': ['8000:8000']}
port = 8100
w = 0
for _ in range(1, 6):
    w += 1
    t =  0
    for _ in range(1, 6):
        t += 1
        print(f"{w} w , {t} t, {port} port")
        _sample = sample.copy()
        _sample['ports'] = [f"{port}:8000"]
        _sample['environment']['THREADS'] = t
        _sample['environment']['WORKERS'] = w
        compose_out['services'][f'app_w{w}_t{t}'] = _sample
        port += 1
print(json.dumps(compose_out, indent=2, sort_keys=True))
with open('../docker-compose_workers_and_threads.yml', 'w') as f:
    # don't add &id001
    yaml.Dumper.ignore_aliases = lambda self, data: True
    yaml.dump(compose_out, f, Dumper=yaml.Dumper, default_flow_style=False)
