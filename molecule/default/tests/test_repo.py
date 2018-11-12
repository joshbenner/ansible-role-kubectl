import os

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('repo')

def test_kubectl_installed(host):
    p = host.package('kubectl')
    assert p.is_installed
    assert p.version.startswith('1.9.1')
