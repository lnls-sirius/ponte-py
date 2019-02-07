#!/usr/bin/python3
# -*- coding: utf-8 -*-
from epics import caput, caget
import sys, os

file_name = "ps-list.txt"



base_dir = os.path.dirname(os.path.realpath(__file__))
data_file = os.path.join(base_dir, file_name)
BBB_PS_list = {}
with open(data_file, 'r') as f:
    for current_line in f:
        BBB_PS_list[current_line.split()[0]] = current_line.split()[1:]



if len(sys.argv) == 2:
    if sys.argv[1] in BBB_PS_list:
        if any(caget(ps+":BSMPComm-Sel") for ps in BBB_PS_list[sys.argv[1]]):
            for ps in BBB_PS_list[sys.argv[1]]:
                caput(ps+":BSMPComm-Sel", 0)
        else:
            for ps in BBB_PS_list[sys.argv[1]]:
                caput(ps+":BSMPComm-Sel", 1)
    else:
        sys.stdout.write("Hostname {} not found.", sys.argv[1])
        sys.stdout.flush()

else:
    sys.stdout.write("Run ponte.py HOSTNAME")
    sys.stdout.flush()
