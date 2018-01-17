# kubectl

[![Build Status](https://travis-ci.org/joshbenner/ansible-role-kubectl.svg?branch=master)](https://travis-ci.org/joshbenner/ansible-role-kubectl)

Install kubectl binary and provide kubectl action plugins.

**NOTE:** If you do not wish the role to install kubectl make sure to set `kubectl_install` to `no`.

## License

BSD

## Actions

### kubectl_get

Retrieve object details from a cluster.

| Parameter  | Description                                     |
|:-----------|:------------------------------------------------|
| kubeconfig | Path to kubectl config file to use. Required.   |
| context    | Which kubeconfig context to use. Required.      |
| namespace  | The namespace of resource. (default: `default`) |
| kind       | The kind of resource to retrieve. Required.     |
| name       | Name of the resource to retrieve. Required.     |

The result of the action will contain an `object` attribute with the
retrieved Kubernetes resource.

```yaml
- name: Get current ConfigMap
  kubectl_get:
    kubeconfig: /root/.kube/config
    context: minikube
    namespace: my-namespace
    kind: ConfigMap
    name: foo-config
  register: foo_config
```

### kubectl_apply

| Parameter  | Description                                   |
|:-----------|:----------------------------------------------|
| kubeconfig | Path to kubectl config file to use. Required. |
| context    | Which kubeconfig context to use. Required.    |
| namespace  | The namespace to apply to.                    |
| file       | Path to the YAML file to apply.               |
| data       | Structured YAML data to apply.                |
| raw        | Raw text to apply.                            |

**NOTE:** Only one of `file`, `data`, or `raw` may be used.

```yaml
- name: Update ConfigMap
  kubectl_apply:
    kubeconfig: /root/.kube/config
    context: minikube
    namespace: my-namespace
    data:
      kind: ConfigMap
      apiVersion: v1
      metadata:
        name: foo-config
      data:
        foo: bar
        debug: true

- name: Update Deployment
  kubectl_apply:
    kubeconfig: /root/.kube/config
    context: minikube
    namespace: my-namespace
    file: manifests/foo-deployment.yml
```

### kubectl_delete

| Parameter  | Description                                   |
|:-----------|:----------------------------------------------|
| kubeconfig | Path to kubectl config file to use. Required. |
| context    | Which kubeconfig context to use. Required.    |
| namespace  | The namespace to delete to.                    |
| file       | Path to the YAML file to delete.               |
| data       | Structured YAML data to delete.                |
| raw        | Raw text to delete.                            |

**NOTE:** Only one of `file`, `data`, or `raw` may be used.

```yaml
- name: Deltee ConfigMap
  kubectl_delete:
    kubeconfig: /root/.kube/config
    context: minikube
    namespace: my-namespace
    data:
      kind: ConfigMap
      apiVersion: v1
      metadata:
        name: foo-config
      data:
        foo: bar
        debug: true

- name: Delete Deployment
  kubectl_delete:
    kubeconfig: /root/.kube/config
    context: minikube
    namespace: my-namespace
    file: manifests/foo-deployment.yml
```

**WARNING**: _Ansible_ will not report a change on failure. If you are using `raw` with _multiple resource definitions_, _changes_ will not be reported so make sure to check the `traceback` for more information.

### kubectl_cluster

Update kubectl configuration to include (or exclude) a cluster config.

| Parameter       | Description                                                          |
|:----------------|:---------------------------------------------------------------------|
| kubeconfig      | Path to the kubectl config to edit. Required.                        |
| state           | If cluster should be `absent` or `present` (default).                |
| name            | Name of the cluster. Required.                                       |
| cluster         | Cluster to insert. Required for `state=present`.                     |
| fail_on_missing | Fail if kubeconfig is missing, otherwise create it (default: false). |

```yaml
- name: Ensure test cluster is in kubectl config
  kubectl_cluster:
    kubeconfig: "{{ ansible_home }}/.kube/config"
    name: test
    cluster:
      certificate-authority-data: "{{ my-ca-content | b64encode }}"
      server: https://test.example.com

- name: Remove the dev cluster
  kubectl_cluster:
    kubeconfig: "{{ ansible_home }}/.kube/config"
    name: dev
    state: absent
```

### kubectl_user

Update kubectl configuration to include (or exclude) a user.

| Parameter       | Description                                                          |
|:----------------|:---------------------------------------------------------------------|
| kubeconfig      | Path to the kubectl config to edit. Required.                        |
| state           | If the user should be `absent` or `present` (default).               |
| name            | The config name for the user (not same as username). Required.       |
| user            | User to insert. Required for `state=present`.                        |
| fail_on_missing | Fail if kubeconfig is missing, otherwise create it (default: false). |


```yaml
- name: Ensure foo user is in kubectl config
  kubectl_cluster:
    kubeconfig: "{{ ansible_home }}/.kube/config"
    name: foo
    user:
      client-certificate: /path/to/client.crt
      client-key: /path/to/client.key

- name: Remove the dev cluster
  kubectl_cluster:
    kubeconfig: "{{ ansible_home }}/.kube/config"
    name: dev
    state: absent
```
