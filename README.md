# depstack - A wrapper for easily deploying Docker Swarm stacks with dependencies.

# Usage

```
usage: depstack.py [-h] [-n] stack target

Easily deploy Docker Swarm stacks from multiple interdependent YAML files.

positional arguments:
  stack          The stack to deploy.
  target         The target to deploy.

optional arguments:
  -h, --help     show this help message and exit
  -n, --no-deps  Don't deploy dependencies.
```

# Dependencies

- PyYAML
- schema
- Docker Engine (CLI)

# License

This project is licensed under the BSD 3-clause license. See the file
LICENSE.md in this repository for more details.
