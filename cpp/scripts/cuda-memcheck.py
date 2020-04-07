# Copyright (c) 2020, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
import sys
import re
import os
import subprocess
import argparse


def parse_args():
    argparser = argparse.ArgumentParser(
        "Runs googletest unit-tests with cuda-memcheck enabled")
    argparser.add_argument("-exe", type=str, default=None,
                           help="The googletest executable to be run")
    argparser.add_argument("-pwd", type=str, default=None,
                           help="Current directory for running the exe")
    argparser.add_argument("-v", dest="verbose", action="store_true",
                           help="Print verbose messages")
    args = argparser.parse_args()
    if args.exe is None:
        raise Exception("'-exe' is a mandatory option!")
    return args


def run_cmd(cmd, workdir):
    cwd = os.getcwd()
    if workdir:
        os.chdir(workdir)
    result = subprocess.run(cmd, check=False, shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = result.stdout.decode("utf-8").rstrip()
    if workdir:
        os.chdir(cwd)
    return result.returncode, out


def get_testlist(exe, workdir):
    retcode, out = run_cmd("%s --gtest_list_tests" % exe, workdir)
    if retcode != 0:
        print(out)
        raise Exception("Collecting test-list failed! See above errors")
    tests = []
    for line in out.splitlines():
        # only consider fixtures and main tests
        if line[:2] == "  " or line.startswith("Running "):
            continue
        tests.append(line + "*")
    return tests


def run_tests(args, testlist):
    idx = 1
    failed = 0
    total = len(testlist)
    for test in testlist:
        cmd = "cuda-memcheck %s --gtest_filter=%s" % (args.exe, test)
        print("[%d/%d Failed:%d] Checking %s ... " % \
              (idx, total, failed, test), end="")
        retcode, out = run_cmd(cmd, args.pwd)
        print("[%s]" % ("PASS" if retcode == 0 else "FAIL"))
        if retcode != 0:
            if args.verbose:
                print(out)
            failed += 1
        idx += 1
    if failed != 0:
        print("FAIL: %d failed tests out of %d" % (failed, total))
    else:
        print("PASS")
    return failed == 0


def main():
    args = parse_args()
    testlist = get_testlist(args.exe, args.pwd)
    if not run_tests(args, testlist):
        raise Exception("Test failed! See above for errors")
    return


if __name__ == "__main__":
    main()
