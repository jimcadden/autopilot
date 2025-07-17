import itertools

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
        if len(nodes) < 2:
            return []
        return list(zip(nodes, nodes[1:] + [nodes[0]]))

    @staticmethod
    def generate_all_to_all(nodes: list[str]) -> list[tuple[str, str]]:
        """
        Generates an all-to-all (full mesh) pattern.
        - nodes: A list of node names.
        - Returns: A list of (source_node, destination_node) tuples.
        """
        return list(itertools.permutations(nodes, 2))