from typing import List, Set, Tuple, Generator, Dict, Any, Callable
from pybatfish.question import bfq, load_questions
from utils import interface_to_str, interfaces_from_snapshot, remove_interface_in_config
from pybatfish.client.commands import bf_init_snapshot, bf_delete_snapshot
from topology import *
from pybatfish.datamodel.flow import HeaderConstraints, PathConstraints
import subprocess
from policy import *
import os
import shutil
import tempfile
import json
import re
import sys


def reset():
    subprocess.call(["docker", "restart", "batfish"])
    load_questions()


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


class HeimdallEndNodes(Base):
    def get_internal_nodes(self) -> Set[str]:
        return get_reachable_nodes(self.snapshot, set(self.affected_nodes))


class HeimdallNodeIntersect(Base):
    def get_internal_nodes(self) -> Set[str]:
        return get_reachable_nodes_intersect(self.snapshot, set(self.affected_nodes))


class HeimdallInterface(Base):
    def get_internal_nodes(self) -> Set[str]:
        return self.get_internal_interfaces()

    def get_internal_interfaces(self) -> Set[str]:
        t = build_topology(self.snapshot, set(self.affected_nodes), set())
        return t.reachable_nodes


class Harness(object):
    solutions = [
        (Base, "base"),
        (Empty, "empty"),
        (Neighbor, "neighbor"),
        (CrystalNet, "crystal-net"),
        (Heimdall, "heimdall"),
        (HeimdallInterface, "heimdall_interface"),
        (HeimdallEndNodes, "heimdall_end_nodes"),
        (HeimdallNodeIntersect, "heimdall_intersect4")
    ]

    generation_types = {
        "complete": lambda x: x,
        "random-2": lambda x: x[0:2] if len(x) > 2 else x
    }

    def __init__(self, base: str):
        self.base = base
        bf_init_snapshot(base, "exp")
        self.interfaces = interfaces_from_snapshot("exp")
        self.name_idx = 0

    def get_affected_node(self, node: str, snapshot: str, generator: Callable[[List[str]], List[str]]) -> Set[str]:
        affected_node = set()
        self.name_idx += 1
        results = bfq.differentialReachability(pathConstraints=PathConstraints(startLocation="/host[0-9]+/")) \
            .answer(snapshot=snapshot, reference_snapshot="exp").frame()
        for idx, result in results.iterrows():
            if result.Flow.ingressNode is not None and result.Flow.ingressNode != node:
                affected_node.add(result.Flow.ingressNode)
        return set(generator(list(affected_node)))

    def generate_test_case(self, prev_data: Dict[str, Any]) -> Generator[Tuple[str, Set[str], str, str], None, None]:
        for interface_name in self.interfaces:
            for gname, generator in self.generation_types.items():
                [node, _] = interface_name.split(":")
                if "host" in interface_name:
                    continue
                dir = tempfile.TemporaryDirectory()
                shutil.copytree(self.base, dir.name+"/", dirs_exist_ok=True)
                remove_interface_in_config(dir.name, [interface_name])
                snapshot = f"exp_{self.name_idx}"
                bf_init_snapshot(dir.name, f"exp_{self.name_idx}")
                if interface_name in prev_data and gname in prev_data[interface_name]:
                    nodes = prev_data[interface_name][gname]['affected_nodes']
                else:
                    nodes = self.get_affected_node(node, snapshot, generator)
                if len(nodes):
                    yield interface_name, nodes, snapshot, gname

    def run(self):
        output_path = os.path.join(self.base, "raw.json")
        results = json.load(open(output_path))
        idx = 0
        for interface, affected_nodes, snapshot, selection_type in self.generate_test_case(results):
            print(f"Interface {interface} is down.")
            if interface not in results:
                results[interface] = {}
            if selection_type not in results[interface]:
                results[interface][selection_type] = {
                    "affected_nodes": list(affected_nodes),
                    "solutions": {}
                }
            for solution, name in self.solutions:
                if name not in results[interface][selection_type]['solutions']:
                    s = solution(snapshot, list(affected_nodes))
                    internal_nodes = s.get_internal_nodes()
                    results[interface][selection_type]['solutions'][name] = list(internal_nodes)
            json.dump(results, open(output_path, "w"), indent=2)
            bf_delete_snapshot(snapshot)
            idx += 10
            if idx == 15:
                idx = 0
                reset()


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
            reset()
            if interfaces[i] not in output_policy_map:
                output_policy_map[interfaces[i]] = self.check_interfaces([interfaces[i]])
            for j in range(i, len(interfaces)):
                i2 = interfaces[j]
                if "host" in i2:
                    continue
                if i1 == i2:
                    continue
                if f"{i1},{i2}" not in output_policy_map and f"{i2},{i1}" not in output_policy_map:
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


def process_json(snapshot: str):
    bf_init_snapshot(snapshot, "process_json")
    in_file = os.path.join(snapshot, "raw.json")
    out = open(in_file.split(".")[0] + ".csv", 'w')
    output_policy_map = json.load(open("out-policy-map.json"))
    out.write("interface removed, generator,"
              "# affected nodes, solution, # reachable nodes, interface included, "
              "# interface exposed, # violated policies, # nodes exposed\n")
    result = json.load(open(in_file))
    for (i1, generators) in result.items():
        for (gname, case) in generators.items():
            for (solution_name, solution) in case['solutions'].items():
                exposed_interfaces = set()
                exposed_node = set()
                for node in solution:
                    if "host" in node:
                        continue
                    if "None" in node:
                        continue
                    exposed_node.add(node)
                    if solution_name == "heimdall_interface":
                        exposed_interfaces.add(node)
                    else:
                        exposed_interfaces.update(interfaces_from_snapshot("process_json", node))
                if "heimdall_interface" == solution_name:
                    s1 = exposed_interfaces
                elif "heimdall" == solution_name:
                    s2 = exposed_interfaces
                violated_policies = set()
                ori_violated_policies = set(output_policy_map[i1])
                for name_and_interface in exposed_interfaces:
                    i2 = name_and_interface
                    if i1 == i2:
                        continue
                    if f"{i1},{i2}" in output_policy_map:
                        violated_policies.update(output_policy_map[f"{i1},{i2}"])
                    else:
                        violated_policies.update(output_policy_map[f"{i2},{i1}"])
                out.write(f"{i1}, {gname},"
                          f"{len(case['affected_nodes'])}, {solution_name}, "
                          f"{len(list(filter(lambda x: 'host' not in x, solution)))}, "
                          f"{1 if i1.split(':')[0] in solution else 0}, "
                          f"{len(exposed_interfaces)}, {len(violated_policies.difference(ori_violated_policies))},"
                          f"{len(exposed_node)}\n")
        reset()


def remove_links(path: str):
    bf_init_snapshot(path, 'remove_links')
    results = bfq.reachability(pathConstraints=PathConstraints(startLocation="/host[0-9]+/"))\
        .answer(snapshot='remove_links').frame()
    removable_interfaces = set()
    for idx, result in results.iterrows():
        if result.TraceCount <= 1:
            continue
        visited_interfaces = {}
        for trace in result.Traces:
            if trace.disposition == "NO_ROUTE":
                continue
            for hop in trace.hops:
                node = hop.node
                if "host" in node:
                    continue
                for step in hop.steps:
                    interface = None
                    if hasattr(step.detail, "inputInterface"):
                        interface = step.detail.inputInterface
                    elif hasattr(step.detail, "outputInterface"):
                        interface = step.detail.outputInterface
                    if interface is not None:
                        iname = f"{node}:{interface}"
                        if iname not in visited_interfaces:
                            visited_interfaces[iname] = 0
                        visited_interfaces[iname] += 1
        interfaces = list(filter(lambda it: it[1] > 1, visited_interfaces.items()))
        if len(interfaces) > 0:
            removable_interfaces.add(interfaces[0][0])
    print(removable_interfaces)
    remove_interface_in_config(path, list(removable_interfaces))



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


def convert_csv(path: str):
    result = csv.DictReader(open(path), delimiter=",")
    data = {}
    for field in result:
        interface = {}
        for key in field:
            if key in ["interface removed", " solution", " generator"]:
                continue
            if key not in data:
                data[key] = {}
            if field[' generator'] not in data[key]:
                data[key][field[' generator']] = {}
            if field['interface removed'] not in data[key][field[' generator']]:
                data[key][field[' generator']][field['interface removed']] = {}
            data[key][field[' generator']][field['interface removed']][field[' solution']] = field[key]
    for key in data:
        for generator in data[key]:
            w = csv.DictWriter(open(f"{os.path.dirname(path)}/{key.strip()}-{generator.strip()}-{os.path.basename(path)}", "w"),
                               fieldnames=["interface removed", "base", "empty", "neighbor", "crystal-net", "heimdall",
                                           "heimdall_interface", "heimdall_end_nodes", "heimdall_intersect", "heimdall_intersect2",
                                           "heimdall_intersect3", "heimdall_intersect4"])
            w.writeheader()
            for interface in data[key][generator]:
                d = {
                    "interface removed": interface
                }
                for solution in data[key][generator][interface]:
                    d[solution.strip()] = data[key][generator][interface][solution]
                w.writerow(d)


def build_reachability(snapshot: str):
    bf_init_snapshot(snapshot, "reachability")
    out = open(os.path.join(snapshot, "policies.csv"), "w")
    results = bfq.reachability().answer().frame()
    out.write("type,subnet,specifics,source,Destinations,Environments,Status,Sources\n")
    for idx, result in results.iterrows():
        out.write(f"PolicyType.Reachability,0.0.0.0,2,"
                  f"{result.Flow.ingressNode},123 ({result.Flow.dstIp}/32),9,PolicyStatus.HOLDS,123\n")


def merge_two_files(snapshot1: str, snapshot2: str):
    complete = json.load(open(snapshot1))
    r = json.load(open(snapshot2))
    result = {}
    for interface in complete:
        result[interface] = {
            "complete": complete[interface],
            "random-2": r[interface]
        }
    json.dump(result, open("raw.json", "w"))
