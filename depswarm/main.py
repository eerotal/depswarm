#!/usr/bin/env python3

"""A program for easily deploying stacks from multiple YAML files."""

import os
import sys
import subprocess
import shutil
import json
from typing import List
from argparse import ArgumentParser

from depswarm._internal.models.deploymentconfig import DeploymentConfig
from depswarm._internal.exceptions.genericexceptions import \
    UnsupportedVersionException, MissingDependencyException


def deploy(
    deploymentconfig: DeploymentConfig,
    target: str,
    no_deps: bool,
    dry_run: bool
) -> int:
    """Deploy a stack and its dependencies.

    :param DeploymentConfig deploymentconfig: The root stack to deploy.
    :param str target: The deployment target to use.
    :param bool no_deps: Don't deploy dependencies.

    :return: The return value of 'docker stack deploy'.
    :rtype: int

    :raise ValueError: If there's no partials defined for the stack.
    """

    # Make sure the target can be deployed.
    if target not in deploymentconfig["deploy"]:
        raise ValueError(
            "No target '{}' for stack: {}"
            .format(target, deploymentconfig.path)
        )

    if not no_deps:
        # Deploy dependencies first. DeploymentConfig guarantees there's no
        # circular dependencies.
        if target in deploymentconfig["depends"]:
            for dependency in deploymentconfig["depends"][target]:
                deploy(dependency, target, no_deps, dry_run)

    # Build the shell command for deployment.
    cmd = ["docker", "stack", "deploy"]
    for partial in deploymentconfig["deploy"][target]:
        cmd.extend(["-c", partial])
    cmd.append(deploymentconfig.stack)

    # Deploy the stack.
    print("-- " + " ".join(cmd))

    if not dry_run:
        return subprocess.run(
            " ".join(cmd),
            shell=True,
            check=False
        ).returncode

    return 0


def check_docker():
    """Check that Docker is installed and the version is supported."""

    # Make sure Docker is installed.
    if not shutil.which("docker"):
        raise MissingDependencyException(
            "Docker is required but it's not installed."
        )

    ret = subprocess.run(
        "docker version --format '{{json .}}'",
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    data = json.loads(ret.stdout)

    # Check Docker Client API version.
    client_api_ver = float(data["Client"]["ApiVersion"])
    if client_api_ver < 1.25:
        raise UnsupportedVersionException(
            "Docker Client API {} is not supported; must be >= 1.25."
            .format(client_api_ver)
        )

    # Check Docker Server APi version.
    for c in data["Server"]["Components"]:
        if c["Name"] == "Engine":
            if float(c["Details"]["ApiVersion"]) < 1.25:
                raise UnsupportedVersionException(
                    "Docker Server API {} is not supported; must be >= 1.25."
                    .format(client_api_ver)
                )


def main(argv: List[str]) -> int:
    """Main entrypoint method.

    :param List[str] argv: Command line argument list.

    :return: 0 on success or an error code on failure.
    :rtype: int
    """

    ap = ArgumentParser(
        description=(
            "Easily deploy Docker Swarm stacks from "
            "multiple interdependent YAML files."
        )
    )
    ap.add_argument(
        "-n",
        "--no-deps",
        action="store_true",
        help="Don't deploy dependencies."
    )
    ap.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Dry run; only print commands which would be executed."
    )
    ap.add_argument(
        "stack",
        type=str,
        help="The stack to deploy."
    )
    ap.add_argument(
        "target",
        type=str,
        help="The target to deploy."
    )

    args = ap.parse_args(argv[1:])

    try:
        root = DeploymentConfig(os.path.abspath(args.stack))
    except ValueError as e:
        print("[ERROR] " + str(e))
        return 1
    except FileNotFoundError as e:
        print("[ERROR] " + str(e))
        return 1
    except KeyError as e:
        print("[ERROR] " + str(e))
        return 1

    ret = 0
    try:
        ret = deploy(root, args.target, args.no_deps, args.dry_run)
    except ValueError as e:
        print("[ERROR] " + str(e))
        return 1

    return ret


def entrypoint():
    """Python package entrypoint when run as a CLI utility."""

    try:
        check_docker()
    except UnsupportedVersionException as e:
        print("[ERROR] " + str(e))
        sys.exit(1)
    except MissingDependencyException as e:
        print("[ERROR] " + str(e))
        sys.exit(1)

    sys.exit(main(sys.argv))


if __name__ == "__main__":
    entrypoint()
