"""Class for storing deployment configurations."""

import os
from yaml import load, SafeLoader
from schema import Schema, Use, Optional, SchemaError

from depstack._internal.exceptions.deploymentconfigexceptions import *

class DeploymentConfig(dict):
    """Class for storing deployment configurations."""

    def __init__(self, path: str, dependency_chain=[]):
        """Initialize a DepencyConfig.

        :raise CircularDependencyException: If there's a circular dependency.
        """

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
    def path(self) -> str:
        """Get the absolute path of the stack."""
        return self["_path"]

    @property
    def stack(self) -> str:
        """Get the name of the stack."""
        return os.path.basename(os.path.normpath(self.path))

    def resolve_stack(self, stack: str) -> str:
        """Resolve a stack name "relative" to the current stack path.

        See DeploymentConfig.__init__() for exceptions.

        :param str stack: The name of the stack to resolve.

        :return: The DeploymentConfig of the stack.
        :rtype: DeploymentConfig
        """

        base = os.path.normpath(os.path.join(self["_path"], ".."))
        stackpath = os.path.join(base, stack)

        # Copy the dependency chain to avoid polluting parallel
        # dependency chains.
        tmp = self.dependency_chain.copy()
        return DeploymentConfig(stackpath, tmp)

    def resolve_partial(self, partial: str) -> str:
        """Resolve a partial name "relative" to the current stack path.

        :param str partial: The name of the partial to resolve.

        :return: The absolute path to the partial.
        :rtype: str

        :raise ValueError: If the partial name format is invalid.
        :raise FileNotFoundError: If the partial doesn't exist.
        """

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
        """Load a config from file.

        :param str path: The path of the stack directory.

        :raise ValueError: If the path is not absolute.
        :raise FileNotFoundError: If the path doesn't exist.
        :raise FileNotFoundError: If the stack has no configuration file.
        :raise KeyError: If the stack config contains prohibited targets.
        :raise ValueError: If the config file format is invalid.
        """

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
        try:
            config = self.schema.validate(config)
        except SchemaError as e:
            raise ValueError(
                "Invalid config file {}:\n{}"
                .format(path, str(e))
            ) from e

        # The path key is used internally and not allowed.
        if "_path" in config:
            raise KeyError("Target _path not allowed.")

        for k in config:
            self[k] = config[k]
