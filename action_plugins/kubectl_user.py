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
        user = self._task.args.get('user', None)

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

        user_idx = self.obj_index(config['users'], name)
        if state == 'absent':
            if user_idx is not None:
                changed = True
                del config['users'][user_idx]
        else:  # state == 'present'
            if user is None:
                raise AnsibleActionFail('user is required')
            user_element = dict(name=name, user=user)
            if user_idx is None:
                changed = True
                config['users'].append(user_element)
            elif config['users'][user_idx].get('user') != user:
                changed = True
                config['users'][user_idx] = user_element

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
            self._connection._shell.tmpdir = tmp
            remote_src = os.path.join(tmp, kubeconfig)
            self._transfer_file(tmpfile, remote_src)
            res = self._execute_module(
                module_name='copy',
                module_args=dict(
                    src=remote_src,
                    dest=kubeconfig,
                    validate='kubectl --kubeconfig=%s config view'
                ),
                task_vars=task_vars
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
