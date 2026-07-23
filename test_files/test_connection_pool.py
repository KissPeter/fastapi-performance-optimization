import pytest

from compare_container_performance import CompareContainers
from test_base import TestBase


class TestConnectionPool(TestBase):

    @pytest.mark.connection_pool
    def test_sync_pool_small_vs_large(self):
        """Compare small (2) vs large (100) connection pool - sync endpoint"""
        test_config = [
            {
                "name": "pool_2_sync",
                "port": 8032,
                "baseline": True,
                "uri": "/sync_pool/items/",
            },
            {
                "name": "pool_100_sync",
                "port": 8033,
                "baseline": False,
                "uri": "/sync_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_async_pool_small_vs_large(self):
        """Compare small (2) vs large (100) connection pool - async endpoint"""
        test_config = [
            {
                "name": "pool_2_async",
                "port": 8032,
                "baseline": True,
                "uri": "/async_pool/items/",
            },
            {
                "name": "pool_100_async",
                "port": 8033,
                "baseline": False,
                "uri": "/async_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_sync_pool_small_vs_no_external(self):
        """Compare small pool sync vs no external calls (baseline)"""
        test_config = [
            {
                "name": "no_external_sync",
                "port": 8031,
                "baseline": True,
                "uri": "/sync/items/",
            },
            {
                "name": "pool_2_sync",
                "port": 8032,
                "baseline": False,
                "uri": "/sync_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_async_pool_small_vs_no_external(self):
        """Compare small pool async vs no external calls (baseline)"""
        test_config = [
            {
                "name": "no_external_async",
                "port": 8031,
                "baseline": True,
                "uri": "/async/items/",
            },
            {
                "name": "pool_2_async",
                "port": 8032,
                "baseline": False,
                "uri": "/async_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_sync_pool_40_vs_2(self):
        """Compare pool=40 (anyio tokens) vs pool=2 - sync endpoint"""
        test_config = [
            {
                "name": "pool_2_sync",
                "port": 8032,
                "baseline": True,
                "uri": "/sync_pool/items/",
            },
            {
                "name": "pool_40_sync",
                "port": 8073,
                "baseline": False,
                "uri": "/sync_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_sync_pool_80_vs_40(self):
        """Compare pool=80 (w*t=2*40) vs pool=40 (anyio tokens) - sync endpoint"""
        test_config = [
            {
                "name": "pool_40_sync",
                "port": 8073,
                "baseline": True,
                "uri": "/sync_pool/items/",
            },
            {
                "name": "pool_80_sync",
                "port": 8074,
                "baseline": False,
                "uri": "/sync_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_async_pool_40_vs_2(self):
        """Compare pool=40 (anyio tokens) vs pool=2 - async endpoint"""
        test_config = [
            {
                "name": "pool_2_async",
                "port": 8032,
                "baseline": True,
                "uri": "/async_pool/items/",
            },
            {
                "name": "pool_40_async",
                "port": 8073,
                "baseline": False,
                "uri": "/async_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_async_pool_80_vs_40(self):
        """Compare pool=80 (w*t=2*40) vs pool=40 (anyio tokens) - async endpoint"""
        test_config = [
            {
                "name": "pool_40_async",
                "port": 8073,
                "baseline": True,
                "uri": "/async_pool/items/",
            },
            {
                "name": "pool_80_async",
                "port": 8074,
                "baseline": False,
                "uri": "/async_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()

    @pytest.mark.connection_pool
    def test_sync_pool_80_vs_100(self):
        """Compare pool=100 (over-provisioned) vs pool=80 (w*t) - sync endpoint"""
        test_config = [
            {
                "name": "pool_80_sync",
                "port": 8074,
                "baseline": True,
                "uri": "/sync_pool/items/",
            },
            {
                "name": "pool_100_sync",
                "port": 8033,
                "baseline": False,
                "uri": "/sync_pool/items/",
            },
        ]
        p = CompareContainers(test_config)
        p.run_test()
        p.sum_container_results()
