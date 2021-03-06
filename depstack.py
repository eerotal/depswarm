#!/usr/bin/env python3

"""A script which makes deploying stacks from multiple .yml files a bit simpler."""

import os
import sys
import subprocess
from typing import List

from schema import SchemaError

from depstack._internal.models.deploymentconfig import DeploymentConfig

def deploy(deploymentconfig: DeploymentConfig, target: str):
    # Make sure the target can be deployed.
    if target not in deploymentconfig["deploy"]:
        raise ValueError(
            "No partials defined for: {}"
            .format(deploymentconfig.path)
        )

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
    print("")
    print("Running: " + " ".join(cmd))
    return subprocess.run(" ".join(cmd), shell=True, check=False).returncode

def main(argv: List[str]) -> int:
    """Main entrypoint method."""

    try:
        root = DeploymentConfig(os.path.abspath(argv[1]))
    except SchemaError as e:
        for s in e.autos:
            if s is not None:
                print("[ERROR] " + s)
        return 1

    return deploy(root, argv[2])

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("[INFO] Usage: depstack.py [STACK] [TARGET]")
        sys.exit(1)

    sys.exit(main(sys.argv))

