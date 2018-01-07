#!/usr/bin/env python

import yaml
import re

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    out_re = re.compile(r'^(?P<kind>[^ ]+) "(?P<name>[^"]+)" (?P<action>.+)$')

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False
        super(ActionModule, self).run(tmp, task_vars)

        context = self._task.args.get('context', None)
        namespace = self._task.args.get('namespace', None)
        filepath = self._task.args.get('file', None)
        data = self._task.args.get('data', None)
        raw = self._task.args.get('raw', None)

        if context is None:
            raise AnsibleActionFail('Context is required')

        non_nulls = sum(int(c is not None) for c in (filepath, data, raw))
        if non_nulls > 1:
            raise AnsibleActionFail('Only one of file, data, or raw accepted')
        elif non_nulls == 0:
            raise AnsibleActionFail('file, data, or raw required')

        if filepath is not None:
            with open(filepath, 'r') as file_to_apply:
                raw = file_to_apply.read()
        elif data is not None:
            raw = yaml.safe_dump(data)

        params = ['--context={}'.format(context), '-f -']
        if namespace is not None:
            params.append('--namespace={}'.format(namespace))

        # Cannot abstract this further, as plugins cannot include from
        # role-provided module utils like modules can.
        module_return = self._execute_module(
            module_name='command',
            module_args=dict(
                _raw_params="kubectl apply {}".format(' '.join(params)),
                stdin=raw
            )
        )

        results = []
        unparsed_lines = []
        changed = False
        for line in module_return['stdout_lines']:
            m = self.out_re.match(line)
            if m:
                results.append(m.groupdict())
                if m.group('action') != 'unchanged':
                    changed = True
            else:
                unparsed_lines.append(line)

        module_return.update(dict(
            changed=changed,
            unparsed_lines=unparsed_lines,
            results=results,
            stdin=raw
        ))
        return module_return
