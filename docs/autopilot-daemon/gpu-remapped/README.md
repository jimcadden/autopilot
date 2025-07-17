# GPU Remapped Rows Health Check

## Purpose

Remapped rows are a hardware-level issue in a GPU where faulty memory cells are "remapped" to a reserved pool of spare memory cells. While this is a self-healing mechanism that can prevent immediate failures, the presence of remapped rows is a strong indicator that the GPU is degrading and is at a higher risk of failure in the future.

The purpose of this health check is to query the GPU for the count of remapped rows. Detecting an increase in remapped rows over time allows us to preemptively identify GPUs that are likely to fail and take them out of service before they cause catastrophic failures.

## Implementation

This check is implemented as a combination of a shell script and a Python entrypoint.

*   **[`remapped-rows.sh`](../../../autopilot-daemon/gpu-remapped/remapped-rows.sh)**: This script uses the `nvidia-smi` command-line utility to query for information about remapped rows. It specifically looks for the count of single-bit and double-bit ECC errors that have been corrected by remapping.
*   **[`entrypoint.py`](../../../autopilot-daemon/gpu-remapped/entrypoint.py)**: This Python script executes the `remapped-rows.sh` script, parses its output to extract the number of remapped rows, and exposes this count as a Prometheus metric.

The workflow is straightforward:
1.  The `autopilot` daemon calls `entrypoint.py`.
2.  `entrypoint.py` runs `remapped-rows.sh`.
3.  The script queries `nvidia-smi`.
4.  `entrypoint.py` parses the output and reports the metrics.

## Metrics

The key metrics produced by this health check are:

*   **`autopilot_gpu_remapped_rows_correctable`**: The number of remapped rows that were correctable.
*   **`autopilot_gpu_remapped_rows_uncorrectable`**: The number of remapped rows that were uncorrectable.

An increase in these metrics over time is a cause for concern. While a small, stable number of remapped rows might be acceptable, a growing number indicates ongoing degradation of the GPU hardware. Policies can be set to automatically drain a node if the remapped row count exceeds a certain threshold.