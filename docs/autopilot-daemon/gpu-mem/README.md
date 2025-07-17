# GPU Memory Health Check

## Purpose

The GPU memory health check is a critical test designed to verify the integrity and functionality of the GPU's onboard memory (VRAM). Memory errors, even if intermittent, can lead to silent data corruption, application crashes, and system instability. This check proactively detects memory issues by running a custom-written CUDA program that performs an exhaustive test of the GPU's memory subsystem.

## Implementation

This health check uses a custom CUDA program, `gpucheck.cu`, which is compiled during the Docker image build process and executed by a Python entrypoint.

*   **[`gpucheck.cu`](../../../autopilot-daemon/gpu-mem/gpucheck.cu)**: This is a CUDA source file containing a program specifically written to test GPU memory. It allocates a large chunk of memory on the GPU, writes a pattern to it, reads it back, and verifies that the data has not been corrupted. This process is repeated to ensure that the memory is stable over time.
*   **[`entrypoint.py`](../../../autopilot-daemon/gpu-mem/entrypoint.py)**: This Python script is responsible for executing the compiled `gpucheck` binary. It runs the test, captures its exit code, and determines whether the test passed or failed.

The workflow is as follows:
1.  The `cudabuild` stage of the [`Dockerfile`](../../../autopilot-daemon/Dockerfile) compiles `gpucheck.cu` into an executable binary.
2.  The main `autopilot` daemon invokes `entrypoint.py`.
3.  `entrypoint.py` runs the `gpucheck` executable.
4.  The script reports the success or failure of the test based on the exit code of `gpucheck`.

## Metrics

The primary outcome of this health check is a pass/fail result, which is exposed as a Prometheus metric.

*   **`autopilot_gpu_memory_check_status`**: This metric will have a value of `1` if the memory check passes and `0` if it fails.

A failure in this check is a strong indication of a hardware fault in the GPU's memory modules. In such cases, the node should be immediately cordoned off and taken out of service for physical inspection and potential replacement of the GPU.