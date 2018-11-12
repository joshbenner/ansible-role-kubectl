import os

import pytest
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('download')


def test_kubeconfig_exists(host):
    f = host.file('/kubeconfig')
    assert f.exists


@pytest.mark.parametrize('path,content,present', [
    ('/kubeconfig', 'added-cluster', True),
    ('/kubeconfig', 'added-user', True),
    ('/kubeconfig', 'added-context', True),
    ('/test_kubeconfig', 'remove_cluster', False),
    ('/test_kubeconfig', 'remove_user', False),
    ('/test_kubeconfig', 'remove_context', False)
])
def test_kubeconfig(host, path, content, present):
    f = host.file(path)
    if present:
        assert content in f.content
    else:
        assert content not in f.content
