#!/usr/bin/env python

import re

from ansible.errors import AnsibleActionFail
from ansible.plugins.action import ActionBase
from ansible.module_utils.basic import jsonify


class ActionModule(ActionBase):
    out_re = re.compile(r'^(?P<kind>[^ ]+) "(?P<name>[^"]+)" (?P<action>.+)$')
    out_not_found_re = re.compile(
        r'^Error from server \(NotFound\): error when stopping'
        ' "(?P<source>[^"]+)": (?P<kind>[^ ]+) "(?P<name>[^"]+)" not found$')

    def run(self, tmp=None, task_vars=None):
        self._supports_check_mode = False
        super(ActionModule, self).run(tmp, task_vars)

        kubeconfig = self._task.args.get('kubeconfig', None)
        context = self._task.args.get('context', None)
        namespace = self._task.args.get('namespace', None)
        filepath = self._task.args.get('file', None)
        data = self._task.args.get('data', None)
        raw = self._task.args.get('raw', None)

        if kubeconfig is None:
            raise AnsibleActionFail('kubeconfig is required')
        if context is None:
            raise AnsibleActionFail('context is required')

        non_nulls = sum(int(c is not None) for c in (filepath, data, raw))
        if non_nulls > 1:
            raise AnsibleActionFail('Only one of file, data, or raw accepted')
        elif non_nulls == 0:
            raise AnsibleActionFail('file, data, or raw required')

        if filepath is not None:
            with open(filepath, 'r') as file_to_apply:
                raw = file_to_apply.read()
        elif data is not None:
            raw = jsonify(data)

        params = [
            '--kubeconfig={}'.format(kubeconfig),
            '--context={}'.format(context),
            'delete',
            '-f -'
        ]
        if namespace is not None:
            params.append('--namespace={}'.format(namespace))

        # Cannot abstract this further, as plugins cannot include from
        # role-provided module utils like modules can.
        module_return = self._execute_module(
            module_name='command',
            module_args=dict(
                _raw_params="kubectl {}".format(' '.join(params)),
                stdin=raw
            )
        )

        results = []
        unparsed_lines = []
        changed = False

        if module_return.get('failed', None):
            failure_count = 0
            for line in module_return['stderr_lines']:
                m = self.out_not_found_re.match(line)
                if m:
                    results.append(m.groupdict())
                else:
                    failure_count += 1
                    unparsed_lines.append(line)
            if failure_count == 0:
                module_return['failed'] = False

        for line in module_return['stdout_lines']:
            m = self.out_re.match(line)
            if m:
                results.append(m.groupdict())
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
