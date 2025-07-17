# GPU Power Throttling Test

## Purpose

The GPU power throttling test is designed to verify the GPU's ability to operate correctly under different power caps. Modern GPUs can have their power limits adjusted to manage energy consumption and thermal output. This test ensures that the GPU remains stable and functional when its power limit is programmatically changed.

This is an important check because a failure to correctly handle power capping can lead to unexpected behavior, such as performance degradation or driver crashes, when power management policies are applied in a production environment.

## Usage

The power throttling test is performed by the `power-throttle.sh` script.

*   **[`power-throttle.sh`](../../../autopilot-daemon/gpu-power/power-throttle.sh)**: This shell script uses the `nvidia-smi` command-line utility to query and set the power limits of the GPU. It likely performs a sequence of operations, such as:
    1.  Reading the default, minimum, and maximum power limits.
    2.  Setting a new power limit (e.g., the minimum allowed).
    3.  Verifying that the new power limit was applied successfully.
    4.  Potentially running a small workload to ensure the GPU is stable at the new power limit.
    5.  Restoring the original power limit.

To run the script manually for testing purposes, you can execute it directly from the command line:

```bash
./power-throttle.sh
```

The script will output information about the steps it is taking and will exit with a non-zero status code if any step fails. The `autopilot-daemon` captures this exit code to determine the health of the GPU's power management subsystem.