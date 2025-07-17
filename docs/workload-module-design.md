# Workload Module Architectural Design

This document outlines the detailed architectural design for a generalized workload module for Autopilot.

## 1. Introduction

The current implementation of network workloads (`iperf3`, `ping`) has led to code duplication and limited extensibility. This design introduces a generalized, abstract workload module to address these issues. It provides a common framework for defining, generating, and executing various workloads, starting with network-related ones.

The key goals of this redesign are:
*   **Reduce Code Duplication:** Abstract common functionalities like node discovery and lifecycle management.
*   **Improve Extensibility:** Make it easy to add new workloads (e.g., `qperf`) and communication patterns.
*   **Standardize Execution:** Provide a unified entrypoint for running any workload.

## 2. File Structure

The new workload module will be organized under the `autopilot-daemon/workloads/` directory.

```
autopilot-daemon/
└── workloads/
    ├── __init__.py
    ├── base.py                  # AbstractBaseWorkload
    ├── network/
    │   ├── __init__.py
    │   ├── iperf3.py            # Iperf3Workload
    │   └── ping.py              # PingWorkload
    ├── patterns.py              # WorkloadPatternGenerator
    └── entrypoint.py            # Unified entrypoint script
```

## 3. Class Diagrams and API Definitions

### 3.1. `AbstractBaseWorkload`

**Location:** `autopilot-daemon/workloads/base.py`

**Description:** An abstract base class that defines the standard interface and lifecycle for all workloads. It handles node discovery and orchestration.

**Class Definition:**
```python
from abc import ABC, abstractmethod

class AbstractBaseWorkload(ABC):
    """
    Abstract base class for all workloads.
    """
    def __init__(self, nodes: list[str], args: dict):
        """
        Initializes the workload.
        - nodes: A list of Kubernetes node names to run the workload on.
        - args: A dictionary of workload-specific arguments.
        """
        self.nodes = nodes
        self.args = args
        self.results = None

    @abstractmethod
    def setup(self):
        """
        Prepares the environment for the workload.
        (e.g., deploying servers, creating configs).
        """
        pass

    @abstractmethod
    def run(self, pattern: list[tuple[str, str]]):
        """
        Executes the workload based on a given communication pattern.
        - pattern: A list of (client, server) tuples.
        """
        pass

    @abstractmethod
    def process_results(self):
        """
        Parses and aggregates the results from the workload execution.
        """
        pass

    @abstractmethod
    def teardown(self):
        """
        Cleans up any resources created during the setup phase.
        """
        pass
```

### 3.2. `Iperf3Workload`

**Location:** `autopilot-daemon/workloads/network/iperf3.py`

**Description:** A concrete implementation of `AbstractBaseWorkload` for the `iperf3` network benchmark.

**Class Definition:**
```python
class Iperf3Workload(AbstractBaseWorkload):
    """
    Iperf3 workload implementation.
    """
    def setup(self):
        """
        Starts iperf3 servers on all participating nodes.
        """
        # Implementation details...

    def run(self, pattern: list[tuple[str, str]]):
        """
        Runs iperf3 clients against servers according to the pattern.
        """
        # Implementation details...

    def process_results(self):
        """
        Collects iperf3 JSON output, parses it, and calculates aggregate bandwidth.
        """
        # Implementation details...

    def teardown(self):
        """
        Stops all iperf3 servers.
        """
        # Implementation details...
```

### 3.3. `PingWorkload`

**Location:** `autopilot-daemon/workloads/network/ping.py`

**Description:** A concrete implementation of `AbstractBaseWorkload` for the `ping` network utility.

**Class Definition:**
```python
class PingWorkload(AbstractBaseWorkload):
    """
    Ping workload implementation.
    """
    def setup(self):
        """
        No-op for ping, as no server is needed.
        """
        pass

    def run(self, pattern: list[tuple[str, str]]):
        """
        Runs ping from client nodes to server nodes.
        """
        # Implementation details...

    def process_results(self):
        """
        Collects ping output and calculates latency/packet loss statistics.
        """
        # Implementation details...

    def teardown(self):
        """
        No-op for ping.
        """
        pass
```

### 3.4. `WorkloadPatternGenerator`

**Location:** `autopilot-daemon/workloads/patterns.py`

**Description:** A utility class to generate different communication patterns for workloads.

**Class Definition:**
```python
class WorkloadPatternGenerator:
    """
    Generates communication patterns for workloads.
    """
    @staticmethod
    def generate_ring(nodes: list[str]) -> list[tuple[str, str]]:
        """
        Generates a ring pattern where each node communicates with the next.
        - nodes: A list of node names.
        - Returns: A list of (source_node, destination_node) tuples.
        """
        # Implementation details...

    @staticmethod
    def generate_all_to_all(nodes: list[str]) -> list[tuple[str, str]]:
        """
        Generates an all-to-all (full mesh) pattern.
        - nodes: A list of node names.
        - Returns: A list of (source_node, destination_node) tuples.
        """
        # Implementation details...

    @staticmethod
    def generate_one_to_all(nodes: list[str], source_node: str) -> list[tuple[str, str]]:
        """
        Generates a one-to-all pattern from a source node.
        - nodes: A list of node names.
        - source_node: The source node.
        - Returns: A list of (source_node, destination_node) tuples.
        """
        # Implementation details...
```

## 4. Data Flow

The following diagram illustrates the data and control flow from the unified entrypoint to the completion of a workload.

```mermaid
graph TD
    A[Unified Entrypoint] --> B{Parse CLI Args: workload, pattern, nodes};
    B --> C{Instantiate Workload};
    C --> D{Instantiate Pattern Generator};
    D --> E{Generate Pattern};
    E --> F[Workload.setup()];
    F --> G[Workload.run(pattern)];
    G --> H[Workload.process_results()];
    H --> I[Workload.teardown()];
    I --> J[Output Results];

    subgraph "entrypoint.py"
        A
        B
    end

    subgraph "Workload Object (e.g., Iperf3Workload)"
        C
        F
        G
        H
        I
        J
    end

    subgraph "patterns.py"
        D
        E
    end
```

**Flow Description:**

1.  **Initiation:** A user or script calls the **Unified Entrypoint** (`entrypoint.py`) with arguments specifying the desired workload (e.g., `iperf3`), communication pattern (e.g., `ring`), and target nodes.
2.  **Instantiation:** The entrypoint parses these arguments and dynamically instantiates the corresponding workload class (e.g., `Iperf3Workload`).
3.  **Pattern Generation:** The entrypoint uses the `WorkloadPatternGenerator` to create the list of (client, server) pairs for the specified pattern.
4.  **Setup:** The entrypoint calls the `setup()` method on the workload object. The workload prepares the cluster nodes (e.g., starts `iperf3` servers).
5.  **Run:** The entrypoint calls the `run()` method, passing the generated pattern. The workload executes the core logic (e.g., `iperf3` clients connect to servers).
6.  **Process Results:** After execution, the `process_results()` method is called to collect, parse, and aggregate the output from all nodes.
7.  **Teardown:** The `teardown()` method is called to clean up all resources (e.g., stop `iperf3` servers).
8.  **Output:** The final, processed results are printed to standard output or saved to a file.

This structured flow ensures that all workloads follow a consistent lifecycle, promoting code reuse and simplifying the addition of new workloads.