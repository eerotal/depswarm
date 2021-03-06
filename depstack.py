#!/usr/bin/env python3

"""A program which makes deploying stacks from multiple .yml files a bit simpler."""

import os
import sys
import subprocess
from typing import List
from argparse import ArgumentParser

from schema import SchemaError

from depstack._internal.models.deploymentconfig import DeploymentConfig

def deploy(deploymentconfig: DeploymentConfig, target: str, no_deps: bool) -> int:
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
                deploy(dependency, target)

    # Build the shell command for deployment.
    cmd = ["docker", "stack", "deploy"]
    for partial in deploymentconfig["deploy"][target]:
        cmd.extend(["-c", partial])
    cmd.append(deploymentconfig.stack)

    # Deploy the stack.
    print("Exec: " + " ".join(cmd))
    return subprocess.run(" ".join(cmd), shell=True, check=False).returncode

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
    ap.add_argument("-n", "--no-deps", action="store_true", help="Don't deploy dependencies.")
    ap.add_argument("stack", type=str, help="The stack to deploy.")
    ap.add_argument("target", type=str, help="The target to deploy.")

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
        ret = deploy(root, args.target, args.no_deps)
    except ValueError as e:
        print("[ERROR] " + str(e))
        return 1

    return ret

if __name__ == "__main__":
    sys.exit(main(sys.argv))

