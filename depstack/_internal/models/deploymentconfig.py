"""Class for storing deployment configurations."""

import os
from yaml import load, SafeLoader
from schema import Schema, Use, Optional, SchemaError

from depstack._internal.exceptions.deploymentconfigexceptions import *

class DeploymentConfig(dict):
    """Class for storing deployment configurations."""

    def __init__(self, path: str, dependency_chain=[]):
        self["_path"] = path
        self.dependency_chain = dependency_chain

        self.schema = Schema({
            Optional("deploy", default={}): {str: [Use(self.resolve_partial)]},
            Optional("depends", default={}): {str: [Use(self.resolve_stack)]}
        })

        # Make sure there are no circular dependencies.
        if self.stack in dependency_chain:
            self.dependency_chain.append(self.stack)
            raise CircularDependencyException(
                "Circular dependency on stack {}. Dependency chain: {}"
                .format(self.stack, " -> ".join(self.dependency_chain))
            )

        # Add this stack to the dependency chain so that stacks after
        # this one also get the correct chain.
        self.dependency_chain.append(self.stack)

        self.from_stack(self["_path"])

    @property
    def path(self):
        return self["_path"]

    @property
    def stack(self):
        return os.path.basename(os.path.normpath(self.path))

    def resolve_stack(self, stack) -> str:
        """Resolve a stack name "relative" to the current stack path."""

        base = os.path.normpath(os.path.join(self["_path"], ".."))
        stackpath = os.path.join(base, stack)

        # Copy the dependency chain to avoid polluting parallel
        # dependency chains.
        tmp = self.dependency_chain.copy()
        return DeploymentConfig(stackpath, tmp)

    def resolve_partial(self, partial) -> str:
        """Resolve a partial name "relative" to the current stack path."""

        base = os.path.normpath(os.path.join(self["_path"], ".."))
        parts = partial.split("/")

        # If the partial is just a filename, try to find it in the current
        # stack. If it's a path with a single / symbol, try to find the
        # it in the stack specified before the / symbol. For example
        #   foo.yml => Search for foo.yml in the current stack.
        #   foo/bar.yml => Search for bar.yml in stack foo.
        partialpath = ""
        if len(parts) == 1:
            partialpath = os.path.join(self["_path"], "stack.d", partial)
        elif len(parts) == 2:
            partialpath = os.path.join(base, parts[0], "stack.d", parts[1])
        else:
            raise ValueError("Invalid partial: {}".format(partial))

        if not os.path.isfile(partialpath):
            raise FileNotFoundError("No such partial: {}".format(partialpath))

        return partialpath

    def from_stack(self, path: str):
        """Load a config from file."""

        path = self["_path"]
        self.clear()
        self["_path"] = path

        if not os.path.isabs(path):
            raise ValueError("Path must be absolute.")

        if not os.path.isdir(path):
            raise FileNotFoundError("Stack {} doesn't exist.".format(path))

        conf_path = os.path.join(path, "deploy.yml")

        if not os.path.isfile(conf_path):
            raise FileNotFoundError("No stack config at {}".format(path))

        # Load the deployment config from file.
        config = None
        with open(conf_path, "r") as f:
            config = load(f, Loader=SafeLoader)

        # Validate the config.
        config = self.schema.validate(config)

        # The path key is used internally and not allowed.
        if "_path" in config:
            raise KeyError("Target _path not allowed.")

        for k in config:
            self[k] = config[k]
