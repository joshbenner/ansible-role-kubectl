#!/usr/bin/env python

# Needed, else 'import copy' gets Ansible's copy module.
from __future__ import absolute_import

import base64
import copy
import tempfile
import os

import yaml

from ansible.plugins.action import ActionBase
from ansible.errors import AnsibleActionFail
from ansible.parsing.yaml.dumper import AnsibleDumper


class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        super(ActionModule, self).run(tmp, task_vars)
        changed = False

        for param in ('kubeconfig', 'name'):
            if self._task.args.get(param, None) is None:
                raise AnsibleActionFail('{} is required'.format(param))

        kubeconfig = self._task.args['kubeconfig']
        state = str(self._task.args.get('state', 'present')).lower()
        name = self._task.args['name']
        fail_on_missing = self._task.args.get('fail_on_missing', False)
        context = self._task.args.get('context', None)

        if state not in ('absent', 'present'):
            raise AnsibleActionFail('state must be "absent" or "present"')

        get_current = self._execute_module('slurp',
                                           module_args=dict(src=kubeconfig))
        if get_current.get('failed'):
            if fail_on_missing:
                raise AnsibleActionFail('kubeconfig not found')
            config = {
                'apiVersion': 'v1',
                'kind': 'Config',
                'preferences': {},
                'clusters': [],
                'users': [],
                'contexts': []
            }
        else:
            config = yaml.load(base64.b64decode(get_current['content']))

        old_config = copy.deepcopy(config)

        context_idx = self.obj_index(config['contexts'], name)
        if state == 'absent':
            if context_idx is not None:
                changed = True
                del config['contexts'][context_idx]
        else:  # state == 'present'
            if context is None:
                raise AnsibleActionFail('context is required')
            context_element = dict(name=name, context=context)
            if context_idx is None:
                changed = True
                config['contexts'].append(context_element)
            elif config['contexts'][context_idx].get('context') != context:
                changed = True
                config['contexts'][context_idx] = context_element

        return_result = dict(
            changed=changed,
            kubeconfig=kubeconfig,
            name=name,
            old_config=old_config,
            new_config=config
        )

        # Create local tmp file with updated kubeconfig contents.
        fd, tmpfile = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'w') as f:
                f.write(yaml.dump(config, Dumper=AnsibleDumper,
                                  allow_unicode=True,
                                  default_flow_style=False))
        except Exception as e:
            os.unlink(tmpfile)
            raise AnsibleActionFail('Failed to write temp file', orig_exc=e)

        if self._play_context.diff:
            return_result['diff'] = [
                self._get_diff_data(kubeconfig, tmpfile, task_vars)
            ]

        if changed and not self._play_context.check_mode:
            if tmp is None:
                created_tmp = True
                tmp = self._make_tmp_path()
            else:
                created_tmp = False
            remote_src = os.path.join(tmp, kubeconfig)
            self._transfer_file(tmpfile, remote_src)
            res = self._execute_module(
                module_name='copy',
                module_args=dict(
                    src=remote_src,
                    dest=kubeconfig,
                    validate='kubectl --kubeconfig=%s config view'
                ),
                task_vars=task_vars,
                tmp=tmp
            )
            if created_tmp:
                self._remove_tmp_path(tmp)
            return_result['copy'] = res
            if res.get('failed'):
                return_result['failed'] = True

        os.unlink(tmpfile)
        return return_result

    @staticmethod
    def obj_index(objects, name):
        """Find index of object based on name."""
        i = 0
        for obj in objects:
            if obj['name'] == name:
                return i
            i += 1
        return None
