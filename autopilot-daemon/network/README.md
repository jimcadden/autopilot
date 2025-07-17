# Network Health Checks

## Purpose

The network health checks are designed to validate the connectivity and performance of the network interfaces on each node. In a distributed system, reliable and high-performance networking is critical for application performance and stability. These checks help ensure that nodes can communicate with each other effectively and that the network bandwidth meets the expected performance targets.

Autopilot provides two main types of network validation tests:

*   **Reachability**: Runs `ping` to verify basic connectivity between all Autopilot pods.
*   **Bandwidth**: Uses `iperf3` to measure the actual network throughput between nodes.

## Components

The network health checks are composed of several Python scripts that work together to orchestrate the tests.

*   **[`ping-entrypoint.py`](./ping-entrypoint.py)**: This is the entrypoint for the `ping`-based reachability test. It discovers all other Autopilot pods in the cluster and performs a `ping` to each of them to ensure they are reachable.

*   **[`iperf3_entrypoint.py`](./iperf3_entrypoint.py)**: This is the main entrypoint for the `iperf3`-based bandwidth tests. It coordinates the process of starting `iperf3` servers and clients across the cluster.

*   **[`iperf3_start_servers.py`](./iperf3_start_servers.py)**: This script is responsible for starting one or more `iperf3` servers on the node, listening on specified ports.

*   **[`iperf3_start_clients.py`](./iperf3_start_clients.py)**: This script starts the `iperf3` clients, which connect to the `iperf3` servers on other nodes to perform the bandwidth test.

*   **[`iperf3_stop_servers.py`](./iperf3_stop_servers.py)**: After the tests are complete, this script is used to gracefully shut down the `iperf3` servers.

## Usage

The network health checks can be invoked via the `autopilot-daemon`'s HTTP API.

### Ping Test

To run the `ping` test, you can send a request to the `/status` endpoint with `check=ping`.

```bash
curl "http://127.0.0.1:3333/status?check=ping"
```

This will trigger the `ping-entrypoint.py` script and report the reachability status of all nodes.

### Iperf3 Bandwidth Test

The `iperf3` test is more complex and involves a "ring workload" pattern to test bandwidth between all pairs of nodes.

#### Ring Workload

A "Ring Workload" is a testing pattern where traffic flows sequentially from one node to the next, forming a logical ring. For a set of nodes `[A, B, C]`, the traffic pattern would be `A -> B`, `B -> C`, and `C -> A`. This is done to systematically test the throughput of each network interface in the cluster.

To run the `iperf3` ring workload, you can use the following `curl` command:

```bash
curl "http://127.0.0.1:3333/iperf?workload=ring&pclients=<NUM_CLIENTS>&startport=<START_PORT>"
```

*   `pclients`: The number of parallel `iperf3` clients to run for each connection.
*   `startport`: The starting port number for the `iperf3` servers.

The results, including `minimum`, `maximum`, `mean`, and `aggregate` bitrates, are logged by the `autopilot-daemon` pod and can be used to identify network performance issues.
