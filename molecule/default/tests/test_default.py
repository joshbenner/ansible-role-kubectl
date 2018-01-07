import os

import pytest
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_kubectl_downloaded(host):
    assert host.file('/usr/local/bin/kubectl-1.9.1').exists


def test_kubectl_executable(host):
    assert host.file('/usr/local/bin/kubectl-1.9.1').mode == 0o755


def test_kubectl_linked(host):
    link = host.file('/usr/local/bin/kubectl')
    assert link.is_symlink
    assert link.linked_to == '/usr/local/bin/kubectl-1.9.1'


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
