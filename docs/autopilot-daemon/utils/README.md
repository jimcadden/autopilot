# Utility Scripts

This directory contains utility scripts that are used to orchestrate and manage the health checks performed by the `autopilot-daemon`.

## `runHealthchecks.py`

*   **[`runHealthchecks.py`](../../../autopilot-daemon/utils/runHealthchecks.py)**

### Purpose

This script is the primary orchestrator for the various health checks. It is responsible for executing the different check entrypoints (e.g., for GPU memory, DCGM, network) in a predefined sequence. It aggregates the results from all the individual checks and determines the overall health status of the node.

### Implementation

`runHealthchecks.py` is typically invoked by the main `autopilot` Go application. It iterates through a configured list of health checks, runs the corresponding Python or shell scripts, and collects their outputs and exit codes. The script is designed to be extensible, allowing new health checks to be easily added to the sequence.

## `briefings.sh`

*   **[`briefings.sh`](../../../autopilot-daemon/utils/briefings.sh)**

### Purpose

The purpose of the `briefings.sh` script is to gather essential system information and logs that can be useful for debugging purposes. When a health check fails, this script can be executed to collect a "briefing package" containing details about the system state at the time of the failure.

This may include:
*   `dmesg` output
*   GPU information from `nvidia-smi`
*   Running processes
*   Network configuration

This information is invaluable for developers and system administrators when diagnosing the root cause of a problem.