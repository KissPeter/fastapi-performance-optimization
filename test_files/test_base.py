import os

import pytest


class TestBase:

    @pytest.fixture(autouse=True)
    def dump_docker_stats(self):
        yield
        os.system("docker stats --no-stream")
