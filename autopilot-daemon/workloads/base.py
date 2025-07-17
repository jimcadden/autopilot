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