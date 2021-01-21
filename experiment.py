from typing import List, Set, Tuple, Generator, Dict, Any
from pybatfish.question import bfq
from utils import interface_to_str, interfaces_from_snapshot, remove_interface_in_config
from pybatfish.client.commands import bf_init_snapshot, bf_delete_snapshot
from topology import build_topology
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints
from policy import *
import os
import shutil
import tempfile
import json
import re


class Base(object):
    def __init__(self, snapshot: str, affected_nodes: List[str]):
        self.snapshot = snapshot
        self.affected_nodes = affected_nodes
        self.interfaces = interfaces_from_snapshot(snapshot)

    def get_internal_interfaces(self) -> Set[str]:
        return self.interfaces

    def get_internal_nodes(self) -> Set[str]:
        interfaces = self.get_internal_interfaces()
        return set([interface.split(":")[0] for interface in interfaces])


class Empty(Base):
    def get_internal_interfaces(self) -> Set[str]:
        return set()


class Neighbor(Base):
    def get_internal_interfaces(self) -> Set[str]:
        affected_interfaces = set()
        for node in self.affected_nodes:
            results = bfq.layer3Edges(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                affected_interfaces.add(interface_to_str(result.Remote_Interface))
        return affected_interfaces


class CrystalNet(Base):
    edge = set()

    def build_directed_graph(self) -> Dict[str, Set[str]]:
        pending_nodes = []
        visited = set()
        poped = set()
        edge = {}
        for interface in self.interfaces:
            node_name = interface.split(":")[0]
            if "border" in node_name:
                pending_nodes.append(node_name)
                visited.add(node_name)
        while len(pending_nodes) > 0:
            node = pending_nodes.pop(0)
            poped.add(node)
            # if node not in edge:
            #     edge[node] = []
            results = bfq.layer3Edges(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                hostname = result.Remote_Interface.hostname
                if hostname not in edge:
                    edge[hostname] = set()
                if hostname not in poped:
                    edge[hostname].add(node)
                if hostname in visited:
                    continue
                pending_nodes.append(hostname)
                visited.add(hostname)
        return edge

    def get_internal_interfaces(self) -> Set[str]:
        edge = self.build_directed_graph()
        pending_nodes = self.affected_nodes.copy()
        affected_interfaces = []
        while len(pending_nodes) > 0:
            node = pending_nodes[0]
            pending_nodes = pending_nodes[1:]
            results = bfq.interfaceProperties(nodes=node).answer(snapshot=self.snapshot).frame()
            for idx, result in results.iterrows():
                affected_interfaces.append(interface_to_str(result.Interface))
            if "border" in node:
                continue
            if node not in edge:
                continue
            for parent in edge[node]:
                pending_nodes.append(parent)
        return set(affected_interfaces)


class Heimdall(Base):
    def get_internal_interfaces(self) -> Set[str]:
        t = build_topology(self.snapshot, set(self.affected_nodes), set())
        return t.reachable_nodes


class Harness(object):

    solutions = [
        (Base, "base"),
        (Empty, "empty"),
        (Neighbor, "neighbor"),
        (CrystalNet, "crystal-net"),
        (Heimdall, "heimdall")
    ]

    def __init__(self, base: str):
        self.base = base
        bf_init_snapshot(base, "exp")
        self.interfaces = interfaces_from_snapshot("exp")
        self.name_idx = 0

    def get_affected_node(self, node: str, snapshot: str) -> Set[str]:
        affected_node = set()
        self.name_idx += 1
        results = bfq.differentialReachability(pathConstraints=PathConstraints(startLocation="/host[0-9]+/")) \
            .answer(snapshot=snapshot, reference_snapshot="exp").frame()
        for idx, result in results.iterrows():
            if result.Flow.ingressNode is not None and result.Flow.ingressNode != node:
                affected_node.add(result.Flow.ingressNode)
        while len(affected_node) > 2:
            affected_node.pop()
        return affected_node

    def generate_test_case(self) -> Generator[Tuple[str, Set[str], str], None, None]:
        for interface_name in self.interfaces:
            [node, interface] = interface_name.split(":")
            if "host" in interface_name:
                continue
            dir = tempfile.TemporaryDirectory()
            shutil.copytree(self.base, dir.name+"/", dirs_exist_ok=True)
            remove_interface_in_config(dir.name, node, interface)
            snapshot = f"exp_{self.name_idx}"
            bf_init_snapshot(dir.name, f"exp_{self.name_idx}")
            nodes = self.get_affected_node(node, snapshot)
            if len(nodes):
                yield interface_name, nodes, snapshot

    def run(self, output_path: str):
        results = json.load(open(output_path))
        # visited = set()
        # rrr = []
        # for result in results:
        #     if result['interface'] not in visited:
        #         visited.add(result['interface'])
        #         rrr.append(result)
        # json.dump(rrr, open("tmp.json", "w"), indent=2)
        # return
        visited = set([result['interface'] for result in results])
        for interface, affected_nodes, snapshot in self.generate_test_case():
            # if "as2border1:GigabitEthernet2/0" in interface:
            #     continue
            if interface in visited:
                continue
            print(f"Interface {interface} is down.")
            result = {
                "interface": interface,
                "affected_nodes": list(affected_nodes),
                "solutions": []
            }
            for solution, name in self.solutions:
                s = solution(snapshot, list(affected_nodes))
                internal_nodes = s.get_internal_nodes()
                result['solutions'].append({
                    "name": name,
                    "internal_nodes": list(internal_nodes),
                })
            visited.add(interface)
            results.append(result)
            json.dump(results, open(output_path, "w"), indent=2)
            bf_delete_snapshot(snapshot)


class VerifyInvariant(object):

    def __init__(self, base: str, in_file: str, policies: str):
        self.base = base
        # policies = build_policies_from_csv(policies)
        bf_init_snapshot(self.base, "base_verify")
        # self.policies = []
        self.policies = load_policies_from_json("policies.json")
        # for policy in policies:
        #     if policy.eval("", "base_verify"):
        #         self.policies.append(policy)
        # json.dump([str(p) for p in self.policies], open("policies.json", "w"))
        self.in_file = in_file
        self.name_idx = 0

    def new_snapshot_name(self, config_path: str):
        self.name_idx += 1
        name = f"verify_exp_{self.name_idx}"
        bf_init_snapshot(config_path, name)
        return name

    def get_violated_policies(self, snapshot: str) -> List[int]:
        violated_policies = set()
        for i in range(len(self.policies)):
            if not self.policies[i].eval("", snapshot):
                violated_policies.add(i)
        return list(violated_policies)

    def check_interfaces(self, node_and_interfaces: [str]) -> List[int]:
        case_base = tempfile.TemporaryDirectory()
        shutil.copytree(self.base, case_base.name + "/", dirs_exist_ok=True)
        remove_interface_in_config(case_base.name, node_and_interfaces)
        case_base_snapshot = self.new_snapshot_name(case_base.name)
        violated_policies = self.get_violated_policies(case_base_snapshot)
        bf_delete_snapshot(case_base_snapshot)
        return violated_policies

    def run(self):
        output_policy_map = json.load(open("out-policy-map.json"))
        interfaces = list(interfaces_from_snapshot("base_verify"))
        for i in range(len(interfaces)):
            i1 = interfaces[i]
            if "host" in i1:
                continue
            if interfaces[i] not in output_policy_map:
                output_policy_map[interfaces[i]] = self.check_interfaces([interfaces[i]])
            for j in range(i, len(interfaces)):
                i2 = interfaces[j]
                if "host" in i2:
                    continue
                if f"{i1},{i2}" not in output_policy_map or f"{i2},{i1}" not in output_policy_map:
                    output_policy_map[f"{i1},{i2}"] = self.check_interfaces([i1, i2])
                json.dump(output_policy_map, open("out-policy-map.json", "w"), indent=2)


        # sanity_check = self.get_violated_policies("base_verify")
        # assert len(sanity_check) == 0
        # interface_map = {}
        # for node_and_interface in interfaces:
        #     [node, _] = node_and_interface.split(":")
        #     if node not in interface_map:
        #         interface_map[node] = set()
        #     interface_map[node].add(node_and_interface)
        #
        # result = json.load(open(self.in_file))
        # for case in result:
        #     [node, interface] = case['interface'].split(':')
        #     case_base = tempfile.TemporaryDirectory()
        #     shutil.copytree(self.base, case_base.name + "/", dirs_exist_ok=True)
        #     remove_interface_in_config(case_base.name, node, interface)
        #     vulnerable_interfaces = set()
        #     for solution in case['solutions']:
        #         for n in solution['internal_nodes']:
        #             if "host" in n:
        #                 continue
        #             vulnerable_interfaces.update(interface_map[n])
        #     #         for node_and_interface in interfaces_from_snapshot("base_verify", node):
        #     #             vulnerable_interfaces.add(node_and_interface)
        #     policy_map = {
        #         "case_violated_policies": case_violated_policies
        #     }
        #     for node_and_interface in vulnerable_interfaces:
        #         [node, interface] = node_and_interface.split(":")
        #         dir = tempfile.TemporaryDirectory()
        #         shutil.copytree(case_base.name, dir.name + "/", dirs_exist_ok=True)
        #         remove_interface_in_config(dir.name, node, interface)
        #         snapshot = self.new_snapshot_name(dir.name)
        #         violated_policies = self.get_violated_policies(snapshot)
        #         policy_map[node_and_interface] = violated_policies
        #         bf_delete_snapshot(snapshot)
        #     output_policy_map[case['interface']] = policy_map
        #     json.dump(output_policy_map, open("out-policy-map.json", "w"))
        #     bf_delete_snapshot(case_base_snapshot)


def process_json(snapshot: str, in_file: str):
    out = open(in_file.split(".")[0] + ".csv", 'w')
    output_policy_map = json.load(open("out-policy-map.json"))
    out.write("interface removed, # affected nodes, solution, # reachable nodes, interface included, "
              "# interface exposed, # violated policies\n")
    result = json.load(open(in_file))
    for case in result:
        for solution in case['solutions']:
            exposed_interfaces = set()
            for node in solution['internal_nodes']:
                if "host" in node:
                    continue
                exposed_interfaces.update(interfaces_from_snapshot(snapshot, node))
            violated_policies = set()
            for name_and_interface in exposed_interfaces:
                i1 = case['interface']
                i2 = name_and_interface
                if f"{i1},{i2}" in output_policy_map:
                    violated_policies.update(output_policy_map[f"{i1},{i2}"])
                else:
                    violated_policies.update(output_policy_map[f"{i2},{i1}"])
            out.write(f"{case['interface']}, {len(case['affected_nodes'])}, {solution['name']}, "
                      f"{len(list(filter(lambda x: 'host' not in x, solution['internal_nodes'])))}, "
                      f"{case['interface'].split(':')[0] in solution['internal_nodes']}, "
                      f"{len(exposed_interfaces)}, {len(violated_policies)}\n")


def remove_links(path: str):
    bf_init_snapshot(path, 'remove_links')
    results = bfq.reachability(pathConstraints=PathConstraints(startLocation="/host[0-9]+/")) \
        .answer(snapshot='remove_links').frame()
    for idx, result in results.iterrows():
        if result.TraceCount <= 1:
            continue
        for trace in result.Traces:
            print(trace)


def generate_hosts(path: str):
    host_template = {
        "hostname": "host3",
        "iptablesFile": "iptables/host_general.iptables",
        "hostInterfaces": {
            "eth0": {
                "name": "eth0",
                "prefix": "2.34.101.101/24",
                "gateway": "2.34.101.3"
            }
        }
    }
    switches = ["as2dept1", "as2dist1", "as2dist2", "as1border2", "as3border2"]
    host_idx = 3
    interface_pattern = re.compile(r"^interface (\w+\/[0-9]+)$")
    ip_pattern = re.compile(r" ip address (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
    host_map = {}
    for switch in switches:
        find_ip = False
        interface_name = None
        for line in open(os.path.join(path, "configs", switch+".cfg")):
            result = interface_pattern.match(line)
            if result is not None:
                find_ip = True
                interface_name = result.group(1)
                continue
            if find_ip:
                result = ip_pattern.match(line)
                if result is not None:
                    interface_ip = result.group(1)
                    segs = interface_ip.split(".")
                    host_template['hostname'] = f"host{host_idx}"
                    host_template['hostInterfaces']['eth0']['gateway'] = interface_ip
                    segs[-1] = "101/24"
                    host_template['hostInterfaces']['eth0']['prefix'] = ".".join(segs)
                    f = open(os.path.join(path, "hosts2", f"host{host_idx}.json"), "w")
                    json.dump(host_template, f, indent=2)
                    host_map[f'host{host_idx}'] = switch + ":" + interface_name
                    host_idx += 1
                if line.strip() == "!":
                    find_ip = False
    json.dump(host_map, open("host-mapping.json", "w"))



