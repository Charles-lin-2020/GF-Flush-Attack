from Ntk_Parser import *
from Ntk_Struct import *
import collections

###########################################################################
# Function name: structure_extract
# Note: search the locked verilog file for the structure c
# input: locked verilog file; number of the keys
# output: structure_extract.txt containing the structure information c
###########################################################################
def structure_extract(verilog_name,num_Key):
    fi = open(verilog_name + '_lock.v')
    f1 = open('c_file.txt', 'w+')  # store the structure information in a file

    for line in fi:
        if 'Kin' in line and 'xor' in line:   # find the feedback logic
            line = line.replace(' ', '')
            line = line.strip(';\n')
            c_list = re.split(r'[=(,)]', line)
            # print(c_list)
            for i in range(num_Key):
                if 'K' + str(i) in c_list:
                    f1.write(str(1) + ',')
                else:
                    f1.write(str(0) + ',')


###########################################################################
# Function name: netlist_extract
# Note: search the locked benchmark file for the key distribution
# input: locked benchmark file; number of the D flip-flops
# output: netlist_extract.txt containing the distribution of keys
###########################################################################
def netlist_extract(Bench_name, num_DFF):
    # parse .bench format netlist into python
    G = ntk_parser(Bench_name + '_lock.bench')
    f1 = open('gate_pos.txt', 'w+')  # store the list of keys in a file

    # do the BFS to find the scan chain, store the DFF nodes in order
    q = collections.deque([])
    visited = set()

    for node in G.object_list:
        if node.name == 'SI':
            q.append(node)
            visited.add(node)

    ordered_FF = []
    scan_gate_list = [4,6,7,9]  # and or xor dff

    while q:
        curnode = q.popleft()

        if curnode.gate_type == 9:
            ordered_FF.append(curnode)
            if len(ordered_FF) == num_DFF:
                break

        for neighbor in curnode.fan_out_node:
            if neighbor not in visited and neighbor.gate_type in scan_gate_list:
                if curnode.gate_type == 9:
                    if neighbor.gate_type == 4 or neighbor.gate_type == 7:
                        q.append(neighbor)
                        visited.add(neighbor)
                if curnode.gate_type == 4:
                    if neighbor.gate_type == 6:
                        q.append(neighbor)
                        visited.add(neighbor)
                if curnode.gate_type == 6:
                    if neighbor.gate_type == 9:
                        q.append(neighbor)
                        visited.add(neighbor)
                if curnode.gate_type == 7 or curnode.name == 'SI':
                    if neighbor.gate_type == 4:
                        q.append(neighbor)
                        visited.add(neighbor)



    # check each DFF to find if it is encrypted
    count = 0
    for node in ordered_FF:
        if node.gate_type == 9 and 'K' not in node.name:
            tag = 0
            for node_fan_out in node.fan_out_node:
                if node_fan_out.gate_type == 7:
                    tag = 1
                    print(count, node.name)
            if tag == 1:
                f1.write(str(count) + ',')
            count = count + 1

# run the main function,
if __name__ == "__main__":
    netlist_extract('s35932', 1728)  # locked benchmark file name, number of DFF
    structure_extract('s35932', 144)    # locked verilog file name, number of key
