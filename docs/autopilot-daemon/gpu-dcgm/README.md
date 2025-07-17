# GPU DCGM Health Check

## Purpose

This health check leverages the NVIDIA Data Center GPU Manager (DCGM) to perform a comprehensive series of diagnostics on the GPUs present in the system. DCGM is a powerful toolset for managing and monitoring NVIDIA GPUs in a cluster environment. By integrating DCGM into Autopilot, we can detect a wide range of potential hardware and software issues before they impact user workloads.

The DCGM health check is designed to be a thorough, low-level validation of the GPU's state, covering everything from memory and SM stress tests to PCIe bus integrity.

## Implementation

The DCGM health check is implemented as a Python script that interfaces with the `nv-hostengine`, the DCGM host agent.

*   **[`entrypoint.py`](../../../autopilot-daemon/gpu-dcgm/entrypoint.py)**: This script is the main entrypoint for the DCGM health check. It uses the `dcgmproftester` tool, which is part of the DCGM suite, to run a series of predefined diagnostic tests. The script initiates the tests, monitors their progress, and collects the results.

The diagnostic level is configurable, allowing for different levels of testing intensity. The results are then parsed and exposed as Prometheus metrics.

## Metrics

The DCGM health check collects a wide variety of metrics that provide deep insights into the health of the GPU. Some of the key metrics include:

*   **`autopilot_dcgm_test_status`**: A summary metric indicating the overall pass/fail status of the DCGM diagnostics.
*   **GPU Temperature**: Monitors the temperature of the GPU to prevent overheating.
*   **Power Usage**: Tracks the power consumption of the GPU, which can be useful for identifying anomalies.
*   **Clock Speeds**: Verifies that the GPU's memory and SM clocks are operating at their expected frequencies.
*   **PCIe Throughput**: Measures the bandwidth of the PCIe bus to ensure it is not a bottleneck.
*   **SM Stress Test**: Runs a compute-intensive workload on the Streaming Multiprocessors (SMs) to check for errors.
*   **Memory Test**: Performs a high-bandwidth memory test to validate the integrity of the GPU's VRAM.

A failure in any of these metrics can trigger an alert, allowing operators to take corrective action, such as draining the node and taking it out of service for repair.