# Autopilot Daemon

## Overview

The `autopilot-daemon` is a core component of the Autopilot ecosystem, designed to run as a [Kubernetes DaemonSet](https://kubernetes.io/docs/concepts/workloads/controllers/daemonset/) on each node in a cluster. Its primary responsibility is to monitor the health of the underlying hardware, particularly GPUs, and report metrics that can be used for automated remediation and node health management. It executes a series of health checks, ranging from simple network tests to complex GPU diagnostics, and exposes the results as Prometheus metrics.

This daemon ensures that nodes are in a healthy state before they are allowed to run workloads and continuously monitors them to detect issues that may arise during operation.

## Architecture

The `autopilot-daemon` consists of a main Go application and a collection of health check scripts written in Python and shell.

*   **Main Go Application**: The primary entrypoint of the daemon, responsible for orchestrating the health checks, interacting with the Kubernetes API, and exposing metrics. The source code can be found in the [`autopilot-daemon/`](../../autopilot-daemon/) directory.
*   **Health Check Scripts**: These are specialized scripts that perform specific health checks. They are located in subdirectories within `autopilot-daemon/`.

A high-level overview of the daemon's architecture can be visualized as follows:

![Autopilot Daemon Pod](../../figures/autopilot-daemon-pod.png)

The main loop of the Autopilot daemon is illustrated here:

![Autopilot Main Loop](../../figures/autopilot-main-loop.svg)

## Getting Started

### Prerequisites

To build and run the `autopilot-daemon`, you will need the following:

*   [Docker](https://docs.docker.com/get-docker/)
*   [Go](https://golang.org/doc/install) (version 1.18 or later)
*   [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit) (for building CUDA-based checks)

### Building the Docker Image

The `autopilot-daemon` is distributed as a Docker image. To build it, use the provided [`Dockerfile`](../../autopilot-daemon/Dockerfile):

```bash
docker build -t autopilot-daemon . -f autopilot-daemon/Dockerfile
```

The [`Dockerfile`](../../autopilot-daemon/Dockerfile) is a multi-stage build:
1.  **`cudabuild` stage**: This stage builds the CUDA-based applications, such as `bandwidthTest` and `gpucheck`.
2.  **`gobuild` stage**: This stage builds the main `autopilot` Go binary.
3.  **Final image**: The final image copies the Go binary and the health check scripts from the previous stages, along with all necessary system dependencies like `iperf3`, `dcgm`, and Python libraries.

### Running the Daemon

The daemon can be run locally for development or deployed as a DaemonSet in a Kubernetes cluster. When running, it requires access to the Docker socket and certain host paths to perform its health checks.

For deployment in a Kubernetes cluster, it is recommended to use the provided [Helm chart](../../helm-charts/autopilot/).

## Configuration

Configuration for the `autopilot-daemon` is managed via command-line flags and environment variables. These options allow you to customize the behavior of the health checks, set thresholds, and configure reporting.

## Health Checks

The `autopilot-daemon` performs a variety of health checks to ensure node health. Below is a summary of the available checks. Each check has its own detailed documentation.

*   [**GPU Bandwidth**](./gpu-bw/README.md): Measures the bandwidth between the host and the GPU.
*   [**GPU DCGM**](./gpu-dcgm/README.md): Uses NVIDIA's Data Center GPU Manager (DCGM) for comprehensive GPU diagnostics.
*   [**GPU Memory**](./gpu-mem/README.md): Checks the integrity of the GPU memory.
*   [**GPU Power**](./gpu-power/README.md): Tests the GPU's ability to operate under different power caps.
*   [**GPU Remapped Rows**](./gpu-remapped/README.md): Checks for remapped rows on the GPU, which can indicate hardware issues.
*   [**Network**](./network/README.md): Performs network connectivity and bandwidth tests.
*   [**Utilities**](./utils/README.md): Utility scripts for orchestrating health checks.

## Dependencies

The `autopilot-daemon` has dependencies on several Go and Python libraries.

*   **Go Dependencies**: The Go dependencies are managed in the [`go.mod`](../../autopilot-daemon/go.mod) file. Key dependencies include:
    *   `k8s.io/*`: For interacting with the Kubernetes API.
    *   `github.com/prometheus/client_golang`: For exposing metrics in Prometheus format.
*   **Python Dependencies**: Python dependencies are installed via `pip` in the `Dockerfile` and include libraries for interacting with system utilities.

## Contributing

We welcome contributions to the `autopilot-daemon`. Please refer to the main project `README.md` for contribution guidelines.

## License

The `autopilot-daemon` is licensed under the Apache 2.0 License. See the [LICENSE](../../LICENSE) file for more details.