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
        cluster = self._task.args.get('cluster', None)

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

        cluster_idx = self.cluster_index(config['clusters'], name)
        if state == 'absent':
            if cluster_idx is not None:
                changed = True
                del config['clusters'][cluster_idx]
        else:  # state == 'present'
            if cluster is None:
                raise AnsibleActionFail('cluster is required')
            cluster_element = dict(name=name, cluster=cluster)
            if cluster_idx is None:
                changed = True
                config['clusters'].append(cluster_element)
            elif config['clusters'][cluster_idx].get('cluster') != cluster:
                changed = True
                config['clusters'][cluster_idx] = cluster_element

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
    def cluster_index(clusters, name):
        """Find index of cluster based on name."""
        i = 0
        for cluster in clusters:
            if cluster['name'] == name:
                return i
            i += 1
        return None
