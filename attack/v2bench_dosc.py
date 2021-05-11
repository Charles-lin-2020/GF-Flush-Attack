import sys
import os
import re
import glob

#=======================================
# This translate function converts verilog circuit to bench format circuit
# Input: verilog file
# Output: bench file
#=======================================

def translate(filePath):
    f = open(filePath, "r")
    benchFilePath = filePath.replace(".v", ".bench")
    #latchnamePath= re.findall("^([\w\d\s\\\/\[\]]+)_locked_netlist.v$", filePath)[0]
    #print (latchnamePath, filePath)
    of = open(benchFilePath, "w+")
    #parsed_f = (f.read()).split(";")
    parsed_f=f.readlines()



    constant_gate = ""
    flipflop_D_ports = []
    flipflop_Q_ports = []
    flipflop_QN_ports = []
    #input_list = []
    #input_visit = []
    
    INPUT_BUS_REGEX = r"^(\s*)input\s+(\s*\[[0-9:]+\][\w\d\s\\\/,]+)+;$"
    BUS_NAME_REGEX = r"\[[0-9:]+\][\w\d\s\\\/]+[,;]" 
    INPUT_REGEX = r"^(\s*)input\s+([\w\d\s\\\/\[\]:,]+)+;$"
    INPUT_NAME_REGEX = r"[\w\d\\\/\[\]]+[,;]"
    OUTPUT_REGEX = r"^(\s*)output\s+([\w\d\s\\\/\[\],]+)+;$"
    OUTPUT_NAME_REGEX = r"[\w\d\\\/\[\]]+[,;]"
    ASSIGN_REGEX = r"^(\s*)assign\s+[\w\d\\\/\[\]]+\s+=\s+[\w\d\'\\\/\[\]]+;$"
    DFF_REGEX = r"^\s*([\w\d]+)\s*<=\s*([\w\d]+);$"
    DIN_REGEX = r"^\s*[\w\d]+\s*<=\s*([\w\d]+);$"
    Q_REGEX = r"^\s*([\w\d]+)\s*<=\s*[\w\d]+;$"
    QN_REGEX = r"\.QN[\s]*\([\w\d\s\\\/\[\]]+\)"
    # match latch
    LATCH_REGEX = r"^(\s*)latchdr[\w\d\s\\\/\[\]]*\([\w\d\s,\(\)\\\/\[\]\'\.]+\);$"
    LATCH_REGEX2="^\s*latchdr\s*([\w\d\s\\\/\[\]]+)\([\w\d\s,\(\)\\\/\[\]\'\.]+\);$"
    LATCH_DIN_REGEX = r"\.D[\s]*\([\w\d\s\\\/\[\]]+\)"
    LATCH_Q_REGEX = r"\.Q[\s]*\([\w\d\s\\\/\[\]]+\)"
    LATCH_QN_REGEX = r"\.QN[\s]*\([\w\d\s\\\/\[\]]+\)"

    # all gates, the first pin is output
    GATE_REGEX = r"^\s*[\w\d]+\s+[\w\d\\\/\[\]\_]+\s*\([\w\d\s,\(\)\\\/\[\]\.]+\);$"
    GATE_TYPE_NAME_REGEX = r"^\s*[\w\d]+\s+[\w\d\\\/\[\]]+"

    DIN_INV_REGEX = r"\s*[\w\d\s\\\/\[\]]+\)"
    Z_REGEX = r"\s*\([\w\d\s\\\/\[\]]+,"

    DIN1_REGEX = r",\s*[\w\d\s\\\/\[\]]+,\s*"
    DIN2_REGEX = r"\s*[\w\d\s\\\/\[\]]+\)"
    #Z_ZN_REGEX = r"\.Q(N?)\([\w\d\s\\\/\[\]]+\)"

    #GATE_PINS_REGEX=r"\s*\([\w\d\s\\\/\[\]]+,\s*[\w\d\s\\\/\[\]]+,\s*[\w\d\s\\\/\[\]]+\);"




    for i in range(len(parsed_f)):
        #parsed_f[i] += ";"
        #parsed_f[i] = parsed_f[i].replace("\n", " ")
        parsed_f[i]=parsed_f[i].rstrip()
        #parsed_f[i] = parsed_f[i].replace("\n", " ").replace("[", "").replace("]", "")

        #------------------------------------
        # Match Bus Input (example: input [9:0] address;)
        #------------------------------------
        if re.match(INPUT_BUS_REGEX, parsed_f[i]):

            x = re.findall(BUS_NAME_REGEX, parsed_f[i])

            for j in range(len(x)):
                y = re.split(r"\[|:|\]| |,|;", x[j])

                for k in range(int(y[1]), int(y[2])+1):
                    of.write("INPUT("+y[-2]+"["+str(k)+"])\n")
                    #input_list.append(str(y[-2]) + "[" + str(k) + "]")
                    #input_visit.append(0)
            continue

        #------------------------------------
        # Match Input (example: input clk, rst;)
        #------------------------------------
        if re.match(INPUT_REGEX, parsed_f[i]): 
            x = re.findall(INPUT_NAME_REGEX, parsed_f[i])
            for j in range(len(x)):
                y = re.sub(r",|;", "", x[j])
                #if (y == "clock") or (y == "clk") or (y == "CLOCK") or (y == "CLK") or (y == "VDD") or (y == "GND"):
                # keep clk
                if (y == "VDD") or (y == "GND"):
                    continue
                of.write("INPUT("+y+")\n")
                #input_list.append(str(y))
                #input_visit.append(0)
                #------------------------------------
                # Construct Constant Gates
                #------------------------------------
                #if constant_gate == "":
                #    constant_gate = str(y)
                #    of.write(str(constant_gate)+"_bar = NOT("+str(constant_gate)+")\n")
                #    of.write("constant_1 = XOR("+str(constant_gate)+", "+str(constant_gate)+"_bar)\n")
                #    of.write("constant_0 = NOT(constant_1)\n")
            continue

        #------------------------------------
        # Match Output
        #------------------------------------
        if re.match(OUTPUT_REGEX, parsed_f[i]): 
            x = re.findall(OUTPUT_NAME_REGEX, parsed_f[i])
            for j in range(len(x)):
                y = re.sub(r",|;", "", x[j])
                of.write("OUTPUT("+y+")\n")
            continue
        
        #------------------------------------
        # Match Assign (example: assign x = 1'b1;)
        #------------------------------------
        if re.match(ASSIGN_REGEX, parsed_f[i]): 
            x = re.split(r"\s+|=|;", parsed_f[i])
            if x[-2] == "1'b1":
                of.write(x[2]+" = XNOR(reset, reset)\n")
            elif x[-2] == "1'b0":
                of.write(x[2]+" = XOR(reset, reset)\n")
            elif x[-2] == "clock" or x[-2] == "clk" or x[-2] == "CLOCK" or x[-2] == "CLK":
                pass
            else:
                of.write(x[2]+" = BUFF("+x[-2]+")\n")
                #if (x[-2]) in input_list:
                    #input_visit[input_list.index(x[-2])] = 1
            continue

        #------------------------------------
        # Match DFF
        #------------------------------------
        if re.match(DFF_REGEX, parsed_f[i]):
            #------------------------------------
            # Match D Port
            #------------------------------------
            D = re.findall(DIN_REGEX, parsed_f[i])
            if (D):
                D_port = D[0]
                #if (D_port) in input_list:
                    #input_visit[input_list.index(D_port)] = 1
            else:
                exit("DIN port doesn't exist!")
            #------------------------------------
            # Match Q Port
            #------------------------------------
            Q = re.findall(Q_REGEX, parsed_f[i])
            Q_port = ""
            if (Q):
                Q_port = Q[0]

                if (D_port in flipflop_D_ports):
                    DFF_index = flipflop_D_ports.index(D_port)
                    if (flipflop_Q_ports[DFF_index] != ""):
                        of.write(Q_port+" = BUFF("+flipflop_Q_ports[DFF_index]+")\n")
                    elif (flipflop_QN_ports[DFF_index] != ""):
                        of.write(Q_port+" = NOT("+flipflop_QN_ports[DFF_index]+")\n")
                else:
                    of.write(Q_port+" = DFF("+D_port+")\n")
            #------------------------------------
            # Match QN Port
            #------------------------------------
            QN = re.search(QN_REGEX, parsed_f[i])
            QN_port = ""
            if (QN):
                QN_port = re.split(r"\(|\)", QN.group())[1].replace(" ", "")
                if (Q):
                    of.write(QN_port+" = NOT("+Q_port+")\n")
                else:
                    if (D_port in flipflop_D_ports):
                        DFF_index = flipflop_D_ports.index(D_port)
                        if (flipflop_QN_ports[DFF_index] != ""):
                            of.write(QN_port+" = BUFF("+flipflop_QN_ports[DFF_index]+")\n")
                        elif (flipflop_Q_ports[DFF_index] != ""):
                            of.write(QN_port+" = NOT("+flipflop_Q_ports[DFF_index]+")\n")
                    else:
                        of.write(QN_port+"_bar = DFF("+D_port+")\n")
                        of.write(QN_port+" = NOT("+QN_port+"_bar)\n")
            flipflop_D_ports.append(D_port)
            flipflop_Q_ports.append(Q_port)
            flipflop_QN_ports.append(QN_port)
            continue


        #------------------------------------
        # Match Latch
        #------------------------------------
        if re.match(LATCH_REGEX, parsed_f[i]):
            x = re.findall(LATCH_REGEX2, parsed_f[i])
            latch_name=x[0]
            #------------------------------------
            # Match D Port
            #------------------------------------
            D = re.search(LATCH_DIN_REGEX, parsed_f[i])
            if (D):
                D_port = re.split(r"\(|\)", D.group())[1]
                #if (D_port) in input_list:
                    #input_visit[input_list.index(D_port)] = 1
            else:
                exit("DIN port doesn't exist!")
            #------------------------------------
            # Match Q Port
            #------------------------------------
            Q = re.search(LATCH_Q_REGEX, parsed_f[i])
            Q_port = ""
            if (Q):
                Q_port = re.split(r"\(|\)", Q.group())[1].replace(" ", "")
                """
                if (D_port in flipflop_D_ports): # deal with 1 pin connecting 2 latches, in our case, we keep all latches
                    DFF_index = flipflop_D_ports.index(D_port)
                    if (flipflop_Q_ports[DFF_index] != ""):
                        of.write(Q_port+" = BUFF("+flipflop_Q_ports[DFF_index]+")\n")
                    elif (flipflop_QN_ports[DFF_index] != ""):
                        of.write(Q_port+" = NOT("+flipflop_QN_ports[DFF_index]+")\n")
                else:
                """
                #print (parsed_f[i])
                if "_L0" in parsed_f[i]:
                    latch_type="L0"
                elif "_L1" in parsed_f[i]:
                    latch_type = "L1"
                elif "_LD" in parsed_f[i]:
                    latch_type = "LD"
                elif "_DD" in parsed_f[i]:
                    latch_type = "DD"
                of.write(Q_port+f" = LATCH_{latch_type}("+D_port+")\n")

            #------------------------------------
            # Match QN Port
            #------------------------------------
            QN = re.search(LATCH_QN_REGEX, parsed_f[i])
            QN_port = ""
            if (QN):
                QN_port = re.split(r"\(|\)", QN.group())[1].replace(" ", "")
                if (Q):
                    of.write(QN_port+" = NOT("+Q_port+")\n")
                else:
                    if (D_port in flipflop_D_ports):
                        DFF_index = flipflop_D_ports.index(D_port)
                        print ("double FF")
                        if (flipflop_QN_ports[DFF_index] != ""):
                            of.write(QN_port+" = BUFF("+flipflop_QN_ports[DFF_index]+")\n")
                        elif (flipflop_Q_ports[DFF_index] != ""):
                            of.write(QN_port+" = NOT("+flipflop_Q_ports[DFF_index]+")\n")
                    else:
                        of.write(QN_port+"_bar = DFF("+D_port+")\n")
                        of.write(QN_port+" = NOT("+QN_port+"_bar)\n")
            flipflop_D_ports.append(D_port)
            flipflop_Q_ports.append(Q_port)
            flipflop_QN_ports.append(QN_port)
            continue

        #------------------------------------
        # Match Gates (NAND, AND, NOR, OR, XOR, XNOR, INV, BUF)
        #------------------------------------
        if re.match(GATE_REGEX, parsed_f[i]) and 'module' not in parsed_f[i]:
            gate = re.match(GATE_TYPE_NAME_REGEX, parsed_f[i])
            gate_type = re.split(r"\s+", gate.group())[1]
            #print (gate_type)

            #------------------------------------
            # For INV (and BUF)
            #------------------------------------
            #if ("hi" in gate_type) or ("ib" in gate_type) or ("nb" in gate_type):
            if ("not" in gate_type):
                #------------------------------------
                # Match DIN Port
                #------------------------------------
                DIN = re.search(DIN_INV_REGEX, parsed_f[i])
                #print (DIN)

                if (DIN):
                    DIN_port = re.split(r"\)", DIN.group())[0].replace(" ", "")
                    #if (DIN_port) in input_list:
                        #input_visit[input_list.index(DIN_port)] = 1
                #print (DIN_port)

                else:
                    exit("DIN port doesn't exist!")
            
                #------------------------------------
                # Match Z/ZN Port
                #------------------------------------
                Z = re.search(Z_REGEX, parsed_f[i])
                #print (Z)

                if (Z):
                    Z_port = re.split(r"\(|,", Z.group())[1].replace(" ", "")
                    #if ("nb" in gate_type):
                    #    of.write(Z_port+" = BUFF("+DIN_port+")\n")
                    #else:
                    if "not" in gate_type:
                        of.write(Z_port+" = NOT("+DIN_port+")\n")
                    #print (Z_port)

                else:
                    exit("Z/ZN port doesn't exist!")
            
            #------------------------------------
            # For NAND, AND, NOR, OR, XOR, XNOR
            #------------------------------------
            else:
                """
                #------------------------------------
                # Match All 3 Ports
                #------------------------------------
                GATE_PINS = re.search(GATE_PINS_REGEX, parsed_f[i])
                if GATE_PINS:
                    #print (re.split(r"\(|\)|,|;", GATE_PINS.group()))
                    PINS=re.split(r"\(|\)|,|;", GATE_PINS.group())
                    Z_port,DIN1,DIN2=PINS[1].replace(" ", ""),PINS[2].replace(" ", ""),PINS[3].replace(" ", "")
                    print (Z_port,DIN1,DIN2)
                else:
                    exit("Gate ports doesn't exist!")
                """
                #------------------------------------
                # Match DIN1 Port
                #------------------------------------
                DIN1 = re.search(DIN1_REGEX, parsed_f[i])

                if (DIN1):
                    DIN1_port = re.split(r",", DIN1.group())[1].replace(" ", "")
                    #if (DIN1_port) in input_list:
                        #input_visit[input_list.index(DIN1_port)] = 1
                    #print (DIN1_port)

                else:
                    #print (parsed_f[i])
                    exit("DIN1 port doesn't exist!")
                #------------------------------------
                # Match DIN2 Port
                #------------------------------------
                DIN2 = re.search(DIN2_REGEX, parsed_f[i])
                if (DIN2):
                    DIN2_port = re.split(r"\)", DIN2.group())[0].replace(" ", "")
                    #if (DIN2_port) in input_list:
                        #input_visit[input_list.index(DIN2_port)] = 1
                    #print (DIN2_port)

                else:
                    exit("DIN2 port doesn't exist!")
                #------------------------------------
                # Match Z/ZN Port
                #------------------------------------
                Z = re.search(Z_REGEX, parsed_f[i])
                if (Z):
                    Z_port = re.split(r"\(|,", Z.group())[1].replace(" ", "")
                    #print (Z_port)

                    gate_type_bench = ""
                    if ("nand" in gate_type):
                        gate_type_bench = "NAND"
                    elif ("xor" in gate_type):
                        gate_type_bench = "XOR"
                    elif ("nor" in gate_type):
                        gate_type_bench = "NOR"
                    elif ("and" in gate_type):
                        gate_type_bench="AND"
                    elif ("or" in gate_type):
                        gate_type_bench="OR"
                    elif ("xnor" in gate_type):
                        gate_type_bench="XNOR"
                    of.write(Z_port+" = "+gate_type_bench+"("+DIN1_port+", "+DIN2_port+")\n")
                else:
                    exit("Z/ZN port doesn't exist!")

    of.close()
    f.close()



if __name__ == "__main__": translate("s35932_lock.v")



