import json
from copy import deepcopy

import yaml


# define a custom representer for strings
def quoted_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(str, quoted_presenter)

compose_out = {"version": "3.1", "services": {}}
test_config = []
sample = {
    "image": "fastapi-performance-optimization:latest",
    "cpus": 2,
    "environment": {"WORKERS": 3, "THREADS": 2},
    "ports": ["8015:8000"],
}
# {'image': 'fastapi-performance-optimization:latest', 'cpus': 2, 'ports': ['8000:8000']}
port = 8100
w = 0
baseline = True
for _ in range(1, 6):
    w += 1
    t = 0
    for _ in range(1, 6):
        t += 1
        cont_id = f"app_w{w}_t{t}"

        print(f"{w} w , {t} t, {port} port")
        _sample = deepcopy(sample)
        _sample["ports"] = [f"{port}:8000"]
        _sample["environment"]["THREADS"] = t
        _sample["environment"]["WORKERS"] = w
        compose_out["services"][cont_id] = _sample
        test_config.append(
            {
                "name": cont_id,
                "port": port,
                "baseline": baseline,
            }
        )
        port += 1
        baseline = False
with open("../docker-compose_workers_and_threads.yml", "w") as f:
    # don't add &id001
    yaml.Dumper.ignore_aliases = lambda self, data: True
    yaml.dump(compose_out, f, Dumper=yaml.Dumper, default_flow_style=False)
print(test_config)
