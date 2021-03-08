# depstack - A wrapper for easily deploying Docker Swarm stacks with dependencies

*depstack* is an opinionated utility command which can be used to deploy Docker
Swarm stacks built from multiple `docker-compose` YAML files. The basic idea is
fairly simple: *depstack* stacks are directories which contain a configuration
file and the YAML stack snippets for the stack in question. The layout of a
*depstack* stack is as follows:

```
custom-stack/
├── deploy.yml
└── stack.d
    ├── stack-1.yml
    └── stack-2.yml
```

Here the name of the stack is `custom-stack`. This also the name of the stack.
*depstack* expects that all stack directories are located in a common root
directory. This is required for dependencies to work.

The example stack directory contains two *docker-compose* stack files in
`stack.d`: `stack-1.yml` and `stack-2.yml`. Ordinarily you might just pass
the separate stack files to `docker stack deploy` using the `-c` flag, but
now *depstack* does all of the work instead. *depstack* also provides some
additinal features which make stack deployment easier.

The directory also contains a file called `deploy.yml`. This is the configuration
file read by *depstack* itself. In short, it declares the stack snippets of the
current stack as well as dependencies on other stacks. The format of the file
is as follows:

```
depends:
  prod:
    - db
    - reverse-proxy
  dev:
    - db
    - reverse-proxy

deploy:
  prod:
    - stack.yml
    - secrets.yml
  dev:
    - stack.yml
    - secrets.yml
```

Following is a description of all the keys you can use in a `deploy.yml` file.

### depends

This key is used to declare any dependencies the stack has on other stacks.
When *depstack* encounters dependencies, it deploys the dependency stacks first
before deploying the stack original stack. Each key in `depends` is a deployment
target which is specified to the *depstack* command when deploying a stack. This
enables you to specify different stack dependencies for example when deploying
to production vs. development. The deployment targets must simply contain a
list of stacks to deploy.

*depstack* expects that all stack directories are located in a common root
directory. Dependencies are deployed in the order they are specified in the
configuration file.

### deploy

This key is used to declare the separate YAML files the stack uses. *depstack*
calls these files *partials*. All *partials* must be located in a directory
called `stack.d` at the root of a stack directory. Each key in `deploy` is a
deployment target which is specified to the *depstack* command when deploying a
stack. This enables you to specify a different stack composition for example
when deploying to production vs. development. The deployment targets must simply
contain a list of file names in `stack.d`.

You can also specify *partials* from other stacks by prefixing the *partial*
name with the name of the stack and a forward slash (/), ie. `stack-2/common.yml`.
This makes it easy to write common partials for multiple stacks without
duplicating a lot of configuration across stacks.

## Usage

Below is the help message printed by `depstack -h`.

```
usage: depstack [-h] [-n] [-d] stack target

Easily deploy Docker Swarm stacks from multiple interdependent YAML files.

positional arguments:
  stack          The stack to deploy.
  target         The target to deploy.

optional arguments:
  -h, --help     show this help message and exit
  -n, --no-deps  Don't deploy dependencies.
  -d, --dry-run  Dry run; only print commands which would be executed.
```

You must run *depstack* in the common root directory where all stack directories
are located. For example, consider the following directory layout:

```
.
├──custom-stack-1/
│  ├── deploy.yml
│  └── stack.d
│      ├── stack-1.yml
│      └── stack-2.yml
└──custom-stack-2/
   ├── deploy.yml
   └── stack.d
       └── stack-3.yml
```

Running `depstack custom-stack-1 prod` in this directory would deploy the `prod`
target of `custom-stack-1`. If `custom-stack-1` depends on `custom-stack-2`,
the latter would be deploy before the former.

## Dependencies

- PyYAML (Python package)
- schema (Python package)
- Docker Engine (System package)

## Development

### Running tests

*depstack* uses [tox](https://tox.readthedocs.io/en/latest/) to automate
linting and other tasks. Install *tox* with

`pip install tox`

By default *tox* tries to use all the environments defined in `tox.ini`, ie.
`pylint` and `pep8`. For example, if you only want to lint the codebase against
PEP-8 you can run

`python3 -m tox -e lint`

You can also use `python` in place of `python3` if both are in your *PATH*.

### CI/CD pipeline

*depstack* uses GitHub Actions for its CI/CD pipeline. Currently the pipeline
automatically lints all commits with *pylint* and *pycodestyle*.

## License

*depstack* is licensed under the BSD 3-clause license. See the file
`LICENSE` in this repository for more details.

Copyright Eero Talus 2021
