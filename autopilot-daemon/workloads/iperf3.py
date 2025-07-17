import asyncio
import json
import logging
import os
import sys
from decimal import Decimal

import aiohttp
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .base import AbstractBaseWorkload

AUTOPILOT_PORT = os.getenv("AUTOPILOT_PORT", 9001)
log = logging.getLogger(__name__)

class Iperf3Workload(AbstractBaseWorkload):
    """
    Iperf3 workload class.
    """

    def __init__(self, nodes: list[str], args: dict):
        super().__init__(nodes, args)
        self.namespace = self.args.get("namespace", os.getenv("NAMESPACE"))
        self.pclients = self.args.get("pclients", "8")
        self.startport = self.args.get("startport", "5200")
        self.node_map = None
        self.raw_results = []
        try:
            config.load_incluster_config()
            self.v1 = client.CoreV1Api()
        except:
            log.error("Failed to load Kubernetes CoreV1API.")
            sys.exit(1)

    def setup(self):
        """
        Prepares the environment for the iperf3 workload.
        """
        log.info("Setting up iperf3 workload")
        self.node_map = self._gen_autopilot_node_map_json()
        asyncio.run(self._iperf_start_servers())

    async def _iperf_start_servers(self):
        """
        Starts iperf3 servers on each node.
        """
        tasks = [
            self._make_server_connection(
                self.node_map[node]["endpoint"],
                f"/iperfservers?numservers={self.pclients}&startport={self.startport}",
            )
            for node in self.node_map
        ]
        await asyncio.gather(*tasks)
        log.info("iPerf3 servers started on all nodes.")

    def run(self, pattern: list[tuple[str, str]]):
        """
        Executes the iperf3 workload based on a given communication pattern.
        """
        log.info(f"Running iperf3 workload with pattern: {pattern}")
        netifaces_count = len(self.node_map[next(iter(self.node_map))]["netifaces"])
        
        for iface in range(netifaces_count):
            log.info(f"Running Interface net1-{iface}")
            self.raw_results.append(asyncio.run(self._run_on_interface(pattern, iface)))

    async def _run_on_interface(self, pattern, iface_index):
        event = asyncio.Event()
        tasks = []
        for source, target in pattern:
            task = self._make_client_connection(
                event,
                f"net1-{iface_index}",
                f"{self.node_map[source]['pod']}_on_{source}",
                f"{self.node_map[target]['pod']}_on_{target}",
                self.node_map[source]["endpoint"],
                f"/iperfclients?dstip={self.node_map[target]['netifaces'][iface_index]}&dstport={self.startport}&numclients={self.pclients}",
            )
            tasks.append(task)
        await asyncio.sleep(1)
        event.set()
        return await asyncio.gather(*tasks)


    def process_results(self):
        """
        Parses and aggregates the results from the workload execution.
        """
        log.info("Processing iperf3 results")
        grids = []
        summary_avg = []
        for i, el in enumerate(self.raw_results):
            grid = {}
            total_bitrate = 0
            count = 0
            for host in el:
                src = host["src"]
                dst = host["dst"]
                if host["data"] == {}:
                    bitrate = 0.0
                else:
                    bitrate = float(
                        host["data"]["receiver"]["aggregate"]["bitrate"]
                    )
                count += 1
                total_bitrate += bitrate
                if src not in grid:
                    grid[src] = {}
                grid[src][dst] = bitrate
            avg = str(round(Decimal(total_bitrate / count), 2)) if count > 0 else "0.0"
            summary_avg.append(f"net1-{i} Average Bandwidth Gb/s: {avg}")
            grids.append(grid)

        for i, grid in enumerate(grids):
            print(f"Network Throughput net1-{i}:")
            pods = sorted(grid.keys())
            print(f"{'src/dst':<40}" + "".join(f"{dst:<40}" for pod in pods))
            for src_pod in pods:
                row = [f"{grid[src_pod].get(dst_pod, 'N/A'):<40}" for dst_pod in pods]
                print(f"{src_pod:<40}" + "".join(row))
            print()

        print("Overall Network Interface Average Bandwidth:")
        for i in summary_avg:
            print(i)
        self.results = grids

    def teardown(self):
        """
        Cleans up any resources created during the setup phase.
        """
        log.info("Tearing down iperf3 workload")
        asyncio.run(self._cleanup_iperf_servers())

    async def _cleanup_iperf_servers(self):
        """
        Removes all started iperf servers across all nodes.
        """
        tasks = [
            self._make_server_connection(
                self.node_map[node]["endpoint"],
                f"/iperfstopservers",
            )
            for node in self.node_map
        ]
        await asyncio.gather(*tasks)
        log.info("iPerf3 servers stopped on all nodes.")

    async def _make_server_connection(self, address, handle):
        url = f"http://{address}:{AUTOPILOT_PORT}{handle}"
        try:
            total_timeout = aiohttp.ClientTimeout(total=60 * 10)
            async with aiohttp.ClientSession(timeout=total_timeout) as session:
                async with session.get(url) as resp:
                    await resp.text()
        except Exception as e:
            log.error(f"Error when creating server on {address} at {handle}: {e}")
            sys.exit(1)

    async def _make_client_connection(self, event, iface, src, dst, address, handle):
        try:
            if event != None:
                await event.wait()
            url = f"http://{address}:{AUTOPILOT_PORT}{handle}"
            total_timeout = aiohttp.ClientTimeout(total=60 * 10)
            async with aiohttp.ClientSession(timeout=total_timeout) as session:
                async with session.get(url) as resp:
                    reply = await resp.text()
                    reply = "".join(reply.split())
                    try:
                        json_reply = json.loads(reply)
                    except json.JSONDecodeError as e:
                        log.error(
                            f"Failed to decode JSON from response: {e}. Response: {reply}"
                        )
                        return {"src": src, "dst": dst, "iface": iface, "data": {}}

                    return {"src": src, "dst": dst, "iface": iface, "data": json_reply}
        except Exception as e:
            log.error(f"Error during client connection to {address} at {handle}: {e}")
            log.error(f"Failure occured with from src {src} to dst {dst} on iface {iface}")
            return {"src": src, "dst": dst, "iface": iface, "data": {}}

    def _gen_autopilot_node_map_json(self):
        try:
            endpoints = self.v1.list_namespaced_endpoints(
                self.namespace,
                field_selector="metadata.name=autopilot-healthchecks",
            )
        except ApiException as e:
            log.error(
                "Exception when calling Kubernetes CoreV1Api->list_namespaced_endpoints: %s\n"
                % e
            )
            sys.exit(1)

        autopilot_node_map = {}
        for endpointslice in endpoints.items:
            if not endpointslice.subsets:
                continue
            addresses = endpointslice.subsets[0].addresses
            for item in addresses:
                node_name = item.node_name
                if node_name not in self.nodes:
                    continue
                if node_name not in autopilot_node_map:
                    pod_name = item.target_ref.name
                    ip_address = item.ip
                    autopilot_node_map[node_name] = {
                        "pod": pod_name,
                        "endpoint": ip_address,
                    }

        addresses = self._get_all_ifaces()
        for add in addresses:
            if add != "eth0":
                for entry in addresses.get(add):
                    worker_node_name = entry[0]
                    net_interfaces = entry[1]
                    if worker_node_name in autopilot_node_map:
                        autopilot_node_map[worker_node_name][
                            "netifaces"
                        ] = net_interfaces
        
        # Filter out nodes that don't have netifaces
        autopilot_node_map = {k: v for k, v in autopilot_node_map.items() if 'netifaces' in v}
        return autopilot_node_map

    def _get_all_ifaces(self):
        address_map = {}
        try:
            autopilot_pods = self.v1.list_namespaced_pod(
                namespace=self.namespace, label_selector="app=autopilot"
            )
        except ApiException as e:
            log.error(
                "Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e
            )
            sys.exit(1)
        
        for pod in autopilot_pods.items:
            if pod.spec.node_name not in self.nodes:
                continue
            entrylist = []
            try:
                entrylist = json.loads(
                    pod.metadata.annotations["k8s.v1.cni.cncf.io/network-status"]
                )
            except (KeyError, TypeError):
                log.info(
                    f'Key k8s.v1.cni.cncf.io/network-status not found on pod "{pod.metadata.name}" on "{pod.spec.node_name}"'
                )
            if len(entrylist) > 0:
                for entry in entrylist:
                    try:
                        iface = entry["interface"]
                    except KeyError:
                        log.info("Interface key name not found, assigning 'k8s-pod-network'.")
                        iface = "k8s-pod-network"
                    if address_map.get(iface) is None:
                        address_map[iface] = []
                    address_map[iface].append((pod.spec.node_name, entry["ips"]))
            else:
                pod_ips = pod.status.pod_ips
                if pod_ips is not None:
                    iface = "default"
                    if address_map.get(iface) is None:
                        address_map[iface] = []
                    ips = [pod_ip.ip for pod_ip in pod_ips]
                    address_map[iface].append((pod.spec.node_name, ips))

        if not address_map:
            log.error("No interfaces found. FAIL.")
        return address_map