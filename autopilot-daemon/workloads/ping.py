import asyncio
import json
import logging
import os
import subprocess
import time
import netifaces

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from .base import AbstractBaseWorkload

log = logging.getLogger(__name__)

class PingWorkload(AbstractBaseWorkload):
    """
    Ping workload class.
    """

    def __init__(self, nodes: list[str], args: dict):
        super().__init__(nodes, args)
        self.namespace = self.args.get("namespace", os.getenv("NAMESPACE"))
        self.nodename_self = os.getenv("NODE_NAME")
        self.raw_results = []
        self.all_nodes_map = {}
        try:
            config.load_incluster_config()
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
        except:
            log.error("Failed to load Kubernetes API.")
            exit(1)

    def setup(self):
        """
        Prepares the environment for the ping workload.
        """
        log.info("Setting up ping workload")
        self._check_local_ifaces()
        self.all_nodes_map = self._get_all_nodes_map()

    def run(self, pattern: list[tuple[str, str]]):
        """
        Executes the ping workload based on a given communication pattern.
        """
        log.info(f"Running ping workload with pattern: {pattern}")
        target_nodes = {target for _, target in pattern}
        
        ifaces = set()
        nodes_to_ping = {}
        for node_name, node_data in self.all_nodes_map.items():
            if node_name in target_nodes:
                nodes_to_ping[node_name] = node_data
                for iface in node_data.keys():
                    ifaces.add(iface)

        if not nodes_to_ping:
            log.warning("No nodes to ping.")
            return

        clients = []
        for nodename, node_data in nodes_to_ping.items():
            for iface in ifaces:
                if iface in node_data:
                    ips = node_data[iface]['ips']
                    for index, ip in enumerate(ips):
                        command = ['ping', ip, '-t', '45', '-c', '10']
                        indexed_iface = f"{iface}-{index}" if len(ips) > 1 else iface
                        clients.append((subprocess.Popen(command, start_new_session=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE), nodename, ip, indexed_iface))

        for c in clients:
            try:
                c[0].wait(50)
            except:
                log.warning(f"Timeout while waiting for {c[2]} on node {c[1]}")
                continue
        
        for c in clients:
            stdout, stderr = c[0].communicate()
            self.raw_results.append({
                "node": c[1],
                "ip": c[2],
                "iface": c[3],
                "stdout": stdout,
                "stderr": stderr
            })

    def process_results(self):
        """
        Parses and aggregates the results from the workload execution.
        """
        log.info("Processing ping results")
        fail = False
        for result in self.raw_results:
            if result["stderr"]:
                log.error(f"[PING] output parse exited with error: {result['stderr']}")
                fail = True
            else:
                if "Unreachable" in result["stdout"] or "100% packet loss" in result["stdout"]:
                    print(f"Node {result['node']} {result['ip']} {result['iface']} 1")
                    fail = True
                else:
                    print(f"Node {result['node']} {result['ip']} {result['iface']} 0")
        
        if fail:
            print("[PING] At least one node unreachable. FAIL")
        else:
            print("[PING] all nodes reachable. success")
        self.results = self.raw_results


    def teardown(self):
        """
        Cleans up any resources created during the setup phase.
        """
        log.info("Tearing down ping workload - no action needed.")
        pass

    def _get_all_nodes_map(self):
        nodes_map = {}
        try:
            retries = 0
            daemonset_size = self._expected_pods()
            autopilot_pods = self.v1.list_namespaced_pod(namespace=self.namespace, label_selector="app=autopilot")
            while len(autopilot_pods.items) < daemonset_size or retries > 100:
                log.info("[PING] Waiting for all Autopilot pods to run")
                time.sleep(5)
                autopilot_pods = self.v1.list_namespaced_pod(namespace=self.namespace, label_selector="app=autopilot")
                retries +=1
            if retries > 100 and len(autopilot_pods.items) < daemonset_size:
                log.error("[PING] Reached max retries of 100. ABORT")
                exit()
        except ApiException as e:
            log.error(f"Exception when calling CoreV1Api->list_namespaced_pod: {e}")
            exit()

        for pod in autopilot_pods.items:
            if pod.spec.node_name != self.nodename_self and pod.spec.node_name in self.nodes:
                node_data = {}
                try:
                    entrylist = json.loads(pod.metadata.annotations['k8s.v1.cni.cncf.io/network-status'])
                    for entry in entrylist:
                        iface = entry.get('interface', 'k8s-pod-network')
                        node_data[iface] = {'ips': entry['ips'], 'pod': pod.metadata.name}
                except (KeyError, TypeError):
                    pod_ips = pod.status.pod_i_ps
                    if pod_ips:
                        node_data['default'] = {'ips': [p.ip for p in pod_ips], 'pod': pod.metadata.name}
                if node_data:
                    nodes_map[pod.spec.node_name] = node_data
        return nodes_map

    def _check_local_ifaces(self):
        podname = os.getenv("POD_NAME")
        pod_list = self.v1.list_namespaced_pod(namespace=self.namespace, field_selector=f"metadata.name={podname}")
        pod_self = pod_list.items[0]
        ip_addresses = [netifaces.ifaddresses(iface)[netifaces.AF_INET][0]['addr'] for iface in netifaces.interfaces() if netifaces.AF_INET in netifaces.ifaddresses(iface)]
        
        try:
            entrylist = json.loads(pod_self.metadata.annotations['k8s.v1.cni.cncf.io/network-status'])
            for entry in entrylist:
                for ip in entry.get('ips', []):
                    if ip not in ip_addresses:
                        log.error(f"[PING] IFACES count inconsistent. Pod annotation reports {entry['ips']}, not found in the pod among {ip_addresses}. ABORT")
                        exit()
        except (KeyError, TypeError):
             pod_ips = pod_self.status.pod_i_ps
             if pod_ips:
                 for pod_ip in pod_ips:
                     if pod_ip.ip not in ip_addresses:
                        log.error(f"[PING] IFACES count inconsistent. Pod annotation reports {pod_ip.ip}, not found in the pod among {ip_addresses}. ABORT")
                        exit()

    def _expected_pods(self):
        try:
            autopilot = self.apps_v1.list_namespaced_daemon_set(namespace=self.namespace, label_selector="app=autopilot")
            return autopilot.items[0].status.desired_number_scheduled
        except ApiException as e:
            log.error(f"[PING] Exception when fetching Autopilot by corev1api->list_namespaced_daemon_set {e}")
            return 0