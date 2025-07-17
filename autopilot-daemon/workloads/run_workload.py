import argparse
import importlib
import json
import os
import sys

# Add the parent directory to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from workloads.patterns import WorkloadPatternGenerator
from workloads.iperf3 import Iperf3Workload
from workloads.ping import PingWorkload

# Dictionary mapping workload names to their classes
WORKLOADS = {
    "iperf3": Iperf3Workload,
    "ping": PingWorkload,
}

def main():
    """
    Unified entrypoint to select and run a workload.
    """
    parser = argparse.ArgumentParser(description="Run a generalized workload.")
    parser.add_argument("--workload", type=str, required=True, choices=WORKLOADS.keys(), help="Name of the workload to run.")
    parser.add_argument("--pattern", type=str, required=True, choices=['ring', 'all-to-all'], help="Communication pattern.")
    parser.add_argument("--nodes", type=str, required=True, help="Comma-separated list of node names.")
    parser.add_argument("--args", type=json.loads, default={}, help="JSON string of workload-specific arguments.")
    
    args = parser.parse_args()

    # Get the workload class from the dictionary
    WorkloadClass = WORKLOADS.get(args.workload)
    if not WorkloadClass:
        print(f"Error: Workload '{args.workload}' not found.")
        sys.exit(1)

    # Prepare nodes and pattern
    nodes = [node.strip() for node in args.nodes.split(',')]
    pattern_generator = WorkloadPatternGenerator()
    
    if args.pattern == 'ring':
        pattern = pattern_generator.generate_ring(nodes)
    elif args.pattern == 'all-to-all':
        pattern = pattern_generator.generate_all_to_all(nodes)
    else:
        print(f"Error: Invalid pattern '{args.pattern}'.")
        sys.exit(1)

    # Instantiate and run the workload
    workload = WorkloadClass(nodes=nodes, args=args.args)
    
    print(f"Setting up workload '{args.workload}'...")
    workload.setup()
    
    print(f"Running workload with '{args.pattern}' pattern...")
    workload.run(pattern)
    
    print("Processing results...")
    workload.process_results()
    
    print("Tearing down workload...")
    workload.teardown()
    
    print("Workload execution complete.")
    if workload.results:
        print("Results:", json.dumps(workload.results, indent=2))

if __name__ == "__main__":
    main()