import re
import numpy as np
import random
from Ntk_Parser import *
from Ntk_Struct import *


###########################################################################
# Function name: scan_lock
# detailed function: generate encrypted scan chain in verilog format
# input: original benchmark file (bench format); number of D flip-flops; number of keys
# output: verilog file with encrypted scan chain
###########################################################################
def scan_lock(Bench_name, num_DFF, num_Key):
    # parse .bench format netlist into python
    G = ntk_parser(Bench_name + '.bench')
    f_key = open('list_Key.txt', 'w+')

    # add new input into the netlist
    test = NtkObject('test')  # input signal 'test'
    test_bar = NtkObject('test_bar')  # input signal 'test_bar'
    SI = NtkObject('SI')              # input signal 'SI': scan_in
    G.add_object(test, 'IPT')         # declare the gate type
    G.add_object(test_bar, 'IPT')
    G.add_object(SI, 'IPT')
    G.PI.append(test)                 # add new nodes into the graph
    G.PI.append(test_bar)
    G.PI.append(SI)

    num = 0  # used for the naming of key
    count_Key = 0  # count the DFF in order

    # select the encrypted DFFs randomly, the selected DFFs are stored in the list_Key
    random.seed(1)
    list_Key = random.sample(range(0, num_DFF-1), num_Key)
    list_Key.sort()
    for key in list_Key:
        f_key.write(str(key) + ' ')
    print(list_Key)

    node_list = []  # list of the output nodes of DFF units(mux + DFF (+ xor))

    for node in G.object_list:
        # add mux : 'Q = D' => 'Q = D * test_bar + SI * test'
        if node.gate_type == 9:   # gate type is DFF
            if count_Key in list_Key:   # if this is the encrypted DFF
                # create new nodes in mux
                new_node1 = NtkObject('Gin' + str(num * 3))
                new_node2 = NtkObject('Gin' + str(num * 3 + 1))
                new_node3 = NtkObject('Gin' + str(num * 3 + 2))
                G.add_object(new_node1, 'AND')
                G.add_object(new_node2, 'AND')
                G.add_object(new_node3, 'OR')

                # create new nodes in  encrypted XOR gate
                key = NtkObject('K' + str(num))
                new_node4 = NtkObject('Gout' + str(num))
                G.add_object(key, 'IPT')
                G.add_object(new_node4, 'XOR')
                G.KI.append(key)

                node_list.append(new_node4)

                # adjust fan_in and fan_out
                for node_fan_in in node.fan_in_node:
                    node_fan_in.fan_out_node.remove(node)
                    node_fan_in.fan_out_node.append(new_node1)
                    new_node1.fan_in_node = [node_fan_in, test_bar]
                    new_node3.fan_in_node = [new_node1, new_node2]
                    new_node4.fan_in_node = [node, key]
                    if num == 0:
                        new_node2.fan_in_node = [SI, test]
                        SI.fan_out_node = [new_node2]
                    else:  # change the content of the list
                        node_list[num - 1].fan_out_node = [new_node2]
                        new_node2.fan_in_node = [node_list[num - 1], test]

                for node_fan_out in node.fan_out_node:
                    node_fan_out.fan_in_node.remove(node)
                    node_fan_out.fan_in_node.append(new_node4)
                    new_node4.fan_out_node.append(node_fan_out)

                test.fan_out_node.append(new_node2)
                test_bar.fan_out_node.append(new_node1)
                node.fan_in_node = [new_node3]
                node.fan_out_node = [new_node4]
                new_node1.fan_out_node = [new_node3]
                new_node2.fan_out_node = [new_node3]
                new_node3.fan_out_node = [node]
                key.fan_out_node = [new_node4]

                num = num + 1

            else:         # if this is the unencrypted DFF
                node_list.append(node)
                # create new nodes in mux
                new_node1 = NtkObject('Gin' + str(num * 3))
                new_node2 = NtkObject('Gin' + str(num * 3 + 1))
                new_node3 = NtkObject('Gin' + str(num * 3 + 2))
                G.add_object(new_node1, 'AND')
                G.add_object(new_node2, 'AND')
                G.add_object(new_node3, 'OR')

                # adjust fan_in and fan_out
                for node_fan_in in node.fan_in_node:
                    node_fan_in.fan_out_node.remove(node)
                    node_fan_in.fan_out_node.append(new_node1)
                    new_node1.fan_in_node = [node_fan_in, test_bar]
                    new_node3.fan_in_node = [new_node1, new_node2]
                    if num == 0:
                        new_node2.fan_in_node = [SI, test]
                        SI.fan_out_node = [new_node2]
                    else:  # change the content of the list
                        node_list[num - 1].fan_out_node = [new_node2]
                        new_node2.fan_in_node = [node_list[num - 1], test]

                test.fan_out_node.append(new_node2)
                test_bar.fan_out_node.append(new_node1)
                node.fan_in_node = [new_node3]
                new_node1.fan_out_node = [new_node3]
                new_node2.fan_out_node = [new_node3]
                new_node3.fan_out_node = [node]

                num = num + 1

            count_Key = count_Key + 1



    # transfer python into verilog
    f1 = open(Bench_name + "_lock.v", 'w+')
    f1.write('module s208(')
    for node in G.PI + G.PO:  # remove KI
        f1.write(node.name + ',')
    f1.write('SO,clk,reset,seed);\n  ')

    # write the ports
    f1.write('input ')
    for node in G.PI:  # remove KI
        f1.write(node.name + ',')
    f1.write('clk,reset;\n  ')
    # write the num_Key-bit input seed
    f1.write('input [0:' + str(num_Key - 1) + '] seed;\n  ')
    f1.write('output ')
    for node in G.PO:
        f1.write(node.name + ',')
    f1.write('SO;\n\n  ')

    # write 1-bit wires
    f1.write('wire Kin,')
    str0 = ''
    for node in G.object_list:
        if node not in G.PI + G.KI + G.PO:
            if node.gate_type != 9:
                str0 = str0 + node.name + ','
    str0 = str0.rstrip(',')
    f1.write(str0 + ',SO_bar;\n  ')

    # write num_Key-bit wire seed
    f1.write('wire [0:' + str(num_Key - 1) + '] seed;\n  ')

    # write the regs
    f1.write('reg ')
    str0 = ''
    for node in G.KI:  # add KI to reg
        f1.write(node.name + ',')
    for node in G.object_list:
        if node not in G.PI + G.KI + G.PO:
            if node.gate_type == 9:
                str0 = str0 + node.name + ','
    str0 = str0.rstrip(',')
    f1.write(str0 + ';\n\n  ')

    # write combinational logics
    count_G = 0
    for node in G.object_list:
        str1 = ''
        if node.gate_type == 2:  # NOT
            f1.write('not g2_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        elif node.gate_type == 3:  # NAND
            f1.write('nand g3_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        elif node.gate_type == 4:  # AND
            f1.write('and g4_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        elif node.gate_type == 5:  # NOR
            f1.write('nor g5_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        elif node.gate_type == 6:  # OR
            f1.write('or g6_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        elif node.gate_type == 7:  # XOR
            f1.write('xor g7_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        elif node.gate_type == 8:  # XNOR
            f1.write('xnor g8_' + str(count_G) + '(' + node.name)
            for node_fan_in in node.fan_in_node:
                f1.write(', ' + node_fan_in.name)
            f1.write(');\n  ')
        else:
            pass  # BUFF isn't complete
        count_G = count_G + 1
    f1.write('not g10_1(SO_bar, ' + node_list[-1].name + ');\n  ')
    f1.write('not g10_2(SO, SO_bar);\n  ')                            # the scan out signal
    f1.write('xor g11(Kin, K0, K2, K' + str(num_Key - 1) + ');\n')    # the feedback logic of LFSR

    # write sequential logics
    f1.write('\n  always @ ( posedge clk )\n  begin\n  ')
    f1.write('if (reset)\n  begin\n  ')
    for i in range(num_Key):
        f1.write('K' + str(i) + ' <= seed[' + str(i) + '];\n  ')
    f1.write('end\n  else\n  begin\n  ')
    for node in G.object_list:
        if node.gate_type == 9:
            f1.write(node.name + ' <= ')
            for node_fan_in in node.fan_in_node:
                f1.write(node_fan_in.name + ';\n  ')
                f1.write('//' + node.fan_out_node[0].name + '\n  ')
    for i in range(num_Key - 1):
        f1.write('K' + str(i) + ' <= ' 'K' + str(i + 1) + ';\n  ')
    f1.write('K' + str(num_Key - 1) + ' <= Kin;\n  end\n  end\n\n  ')
    f1.write('endmodule')


# run the main function,
if __name__ == "__main__":
    scan_lock('s35932', 1728, 144)  # original benchmark file name, number of DFF, number of key
