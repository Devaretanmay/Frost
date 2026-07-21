"""FROST execution backends."""

import os
from typing import Any
from frost.backends.native import NativeBackend
from frost.backends.docker import DockerBackend


def get_backend(
    image: str = "",
    timeout: int = 3600,
    workdir: str = "",
    force_docker: bool = False,
) -> Any:
    """Auto-select the appropriate execution backend.
    
    Level 0 (Native Execution): Default for local commands, zero latency (~10ms).
    Level 3 (Docker Container): Selected when an explicit container image is provided,
    or when FROST_BACKEND=docker is set in environment.
    """
    use_docker = force_docker or bool(image) or os.environ.get("FROST_BACKEND", "").lower() == "docker"
    if use_docker:
        resolved_image = image or os.environ.get("FROST_IMAGE", "python:3.12")
        return DockerBackend(
            image=resolved_image,
            resource_args=[],
            network_args=[],
            timeout=timeout,
            workdir=workdir,
        )
    return NativeBackend(timeout=timeout, workdir=workdir)
