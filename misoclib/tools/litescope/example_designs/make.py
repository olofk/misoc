#!/usr/bin/env python3

import sys
import os
import argparse
import subprocess
import struct
import importlib

from mibuild.tools import write_to_file
from migen.util.misc import autotype
from migen.fhdl import verilog, edif
from migen.fhdl.structure import _Fragment
from migen.bank.description import CSRStatus
from mibuild import tools
from mibuild.xilinx.common import *

from misoclib.soc import cpuif
from misoclib.tools.litescope.common import *


def _import(default, name):
    return importlib.import_module(default + "." + name)


def _get_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""\
LiteScope - based on Migen.

This program builds and/or loads LiteScope components.
One or several actions can be specified:

clean           delete previous build(s).
build-rtl       build verilog rtl.
build-bitstream build-bitstream build FPGA bitstream.
build-csr-csv   save CSR map into CSV file.

load-bitstream  load bitstream into volatile storage.

all             clean, build-csr-csv, build-bitstream, load-bitstream.
""")

    parser.add_argument("-t", "--target", default="simple", help="Core type to build")
    parser.add_argument("-s", "--sub-target", default="", help="variant of the Core type to build")
    parser.add_argument("-p", "--platform", default=None, help="platform to build for")
    parser.add_argument("-Ot", "--target-option", default=[], nargs=2, action="append", help="set target-specific option")
    parser.add_argument("-Op", "--platform-option", default=[], nargs=2, action="append", help="set platform-specific option")
    parser.add_argument("--csr_csv", default="./test/csr.csv", help="CSV file to save the CSR map into")

    parser.add_argument("action", nargs="+", help="specify an action")

    return parser.parse_args()

# Note: misoclib need to be installed as a python library

if __name__ == "__main__":
    args = _get_args()

    # create top-level Core object
    target_module = _import("targets", args.target)
    if args.sub_target:
        top_class = getattr(target_module, args.sub_target)
    else:
        top_class = target_module.default_subtarget

    if args.platform is None:
        if hasattr(top_class, "default_platform"):
            platform_name = top_class.default_platform
        else:
            raise ValueError("Target has no default platform, specify a platform with -p your_platform")
    else:
        platform_name = args.platform
    platform_module = _import("mibuild.platforms", platform_name)
    platform_kwargs = dict((k, autotype(v)) for k, v in args.platform_option)
    platform = platform_module.Platform(**platform_kwargs)

    build_name = top_class.__name__.lower() + "-" + platform_name
    top_kwargs = dict((k, autotype(v)) for k, v in args.target_option)
    soc = top_class(platform, **top_kwargs)
    soc.finalize()
    memory_regions = soc.get_memory_regions()
    csr_regions = soc.get_csr_regions()

    # decode actions
    action_list = ["clean", "build-csr-csv", "build-bitstream", "load-bitstream", "all"]
    actions = {k: False for k in action_list}
    for action in args.action:
        if action in actions:
            actions[action] = True
        else:
            print("Unknown action: "+action+". Valid actions are:")
            for a in action_list:
                print("  "+a)
            sys.exit(1)

    print("""
      __   _ __      ____
     / /  (_) /____ / __/______  ___  ___
    / /__/ / __/ -_)\ \/ __/ _ \/ _ \/ -_)
   /____/_/\__/\__/___/\__/\___/ .__/\__/
                              /_/

   A small footprint and configurable embedded FPGA
       logic analyzer core powered by Migen

====== Building parameters: ======
LiscopeIO
---------
Width: {}

LiscopeLA
---------
Width: {}
Depth: {}
Subsampler: {}
RLE: {}
===============================""".format(
    soc.io.dw,
    soc.la.dw,
    soc.la.depth,
    str(soc.la.with_subsampler),
    str(soc.la.with_rle)
    )
)

    # dependencies
    if actions["all"]:
        actions["build-csr-csv"] = True
        actions["build-bitstream"] = True
        actions["load-bitstream"] = True

    if actions["build-bitstream"]:
        actions["build-csr-csv"] = True
        actions["build-bitstream"] = True
        actions["load-bitstream"] = True

    if actions["clean"]:
        subprocess.call(["rm", "-rf", "build/*"])

    if actions["build-csr-csv"]:
        csr_csv = cpuif.get_csr_csv(csr_regions)
        write_to_file(args.csr_csv, csr_csv)

    if actions["build-bitstream"]:
        vns = platform.build(soc, build_name=build_name, run=True)
        if hasattr(soc, "do_exit") and vns is not None:
            if hasattr(soc.do_exit, '__call__'):
                soc.do_exit(vns)

    if actions["load-bitstream"]:
        prog = platform.create_programmer()
        prog.load_bitstream("build/" + build_name + platform.bitstream_ext)
