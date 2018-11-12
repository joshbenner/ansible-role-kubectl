import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('download')


def test_kubectl_downloaded(host):
    assert host.file('/usr/local/bin/kubectl-1.9.1').exists


def test_kubectl_executable(host):
    assert host.file('/usr/local/bin/kubectl-1.9.1').mode == 0o755


def test_kubectl_linked(host):
    link = host.file('/usr/local/bin/kubectl')
    assert link.is_symlink
    assert link.linked_to == '/usr/local/bin/kubectl-1.9.1'
