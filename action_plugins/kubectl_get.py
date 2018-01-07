#!/usr/bin/env python

import json

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)

        for param in ('kubeconfig', 'context', 'kind', 'name'):
            if self._task.args.get(param, None) is None:
                raise AnsibleActionFail('{} is required'.format(param))

        kubeconfig = self._task.args.get('kubeconfig', None)
        context = self._task.args.get('context', None)
        namespace = self._task.args.get('namespace', 'default')
        kind = self._task.args.get('kind', None)
        name = self._task.args.get('name', None)

        params = [
            '--kubeconfig={}'.format(kubeconfig),
            '--context={}'.format(context),
            '--namespace={}'.format(namespace),
            'get', kind, name,
            '-o json'
        ]

        # Cannot abstract this further, as plugins cannot include from
        # role-provided module utils like modules can.
        module_return = self._execute_module(
            module_name='command',
            module_args=dict(
                _raw_params="kubectl {}".format(' '.join(params))
            )
        )
        module_return['changed'] = False
        if module_return['rc'] == 0:
            module_return['object'] = json.loads(module_return['stdout'])

        return module_return
