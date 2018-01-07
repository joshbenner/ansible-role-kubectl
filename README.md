# kubectl

Install kubectl binary and provide kubectl action plugins.

## Requirements

System running Ansible must have the `PyYaml` Python package installed.

## License

BSD

## Actions

### kubectl_apply

| Parameter | Description                                |
|:----------|:-------------------------------------------|
| context   | Which kubeconfig context to use. Required. |
| namespace | The namespace to apply to.                 |
| file      | Path to the YAML file to apply.            |
| data      | Structured YAML data to apply.             |
| raw       | Raw text to apply.                         |

```yaml
- name: Update ConfigMap
  kubectl_apply:
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
    namespace: my-namespace
    file: manifests/foo-deployment.yml
```

