# GPU Bandwidth Health Check

## Purpose

This health check is designed to measure the memory bandwidth between the host system (CPU) and the GPU. Consistently low or fluctuating bandwidth can be an indicator of underlying issues with the PCIe bus, the GPU itself, or the system's motherboard. By monitoring this metric, we can proactively detect hardware problems that might otherwise lead to degraded application performance or system instability.

## Implementation

The GPU bandwidth test is orchestrated by a combination of a shell script and a Python entrypoint, which execute a compiled CUDA sample.

*   **[`gpuLocalBandwidthTest.sh`](../../../autopilot-daemon/gpu-bw/gpuLocalBandwidthTest.sh)**: This script is responsible for invoking the `bandwidthTest` executable, which is a standard NVIDIA CUDA sample. It ensures that the test is run with the correct parameters and that its output is captured for analysis.
*   **[`entrypoint.py`](../../../autopilot-daemon/gpu-bw/entrypoint.py)**: This Python script serves as the main entrypoint for the health check. It calls `gpuLocalBandwidthTest.sh`, parses the output from the `bandwidthTest`, and formats the results into metrics that can be exposed to Prometheus.
*   **`bandwidthTest`**: This is a compiled binary from the NVIDIA CUDA samples. It performs a series of memory copy operations between the host and the device to measure the bandwidth in GB/s.

The workflow is as follows:
1.  The main `autopilot` daemon calls `entrypoint.py`.
2.  `entrypoint.py` executes `gpuLocalBandwidthTest.sh`.
3.  The script runs the `bandwidthTest` executable.
4.  `entrypoint.py` parses the output and exposes the relevant metrics.

## Metrics

The primary metric collected by this health check is the **Host to Device** and **Device to Host** bandwidth, measured in gigabytes per second (GB/s).

*   **`autopilot_gpu_bandwidth_host_to_device_gbs`**: The measured bandwidth for memory transfers from the host to the GPU.
*   **`autopilot_gpu_bandwidth_device_to_host_gbs`**: The measured bandwidth for memory transfers from the GPU to the host.

These metrics are essential for identifying bottlenecks in the data path to and from the GPU. A significant drop in these values can indicate a problem that requires further investigation.