"""
Simon Leary
6/19/2022
Filesystem Responsiveness Checker

Read DIR_LIST_FILE which is a list of directories, make a thread for each
per thread, os.listdir() and see how long it takes
print the results if that time is greater than MIN_REPORT_TIME_S
unless DO_SURPRESS_NORMAL_TIMES==False, then it always prints
"""
import os
import time
import datetime
from threading import Thread

DO_SURPRESS_NORMAL_TIMES = True
DO_SURPRESS_TIMESTAMPS = False
DIR_LIST_FILE = '/opt/nfs-checker/dirs_to_check.txt'
MIN_REPORT_TIME_S = 0.25
LOOP_WAIT_TIME_S = 1

def now_str(time_only=False):
    """
    does not use colons because colons aren't allowed in filenames
    """
    _format = '%Y-%m-%d_%H-%M-%S'
    if time_only:
        _format = '%I-%M-%S'
    return datetime.datetime.now().strftime(_format)

def make_daemon_thread(function, thread_name="anon_thread"):
    """
    does not join()
    """
    Thread(target=function, daemon=True, name=thread_name).start()

class DirChecker:
    def __init__(self, check_dir):
        self.check_dir = check_dir

    def check_time(self):
        before = datetime.datetime.now()
        os.listdir(self.check_dir)
        after = datetime.datetime.now()
        duration_s = (after - before).total_seconds()
        if not DO_SURPRESS_NORMAL_TIMES or duration_s > MIN_REPORT_TIME_S:
            if DO_SURPRESS_TIMESTAMPS:
                print(f"{round(duration_s, 5)} sec", self.check_dir, sep='\t')
            else:
                print(now_str(), f"{round(duration_s, 5)} sec", self.check_dir, sep='\t')

    def check_loop(self):
        while True:
            self.check_time()
            time.sleep(LOOP_WAIT_TIME_S)

if __name__=='__main__':
    dir_list = open(DIR_LIST_FILE, 'r', encoding='utf-8').readlines()
    dir_list = [ dir.replace('\n', '') for dir in dir_list] # remove newlines

    checkers = []
    for _dir in dir_list:
        checkers.append(DirChecker(_dir))

    for (i, checker) in enumerate(checkers):
        make_daemon_thread(checker.check_loop, f'checker{i}')

    # wait so that threads don't kill
    while True:
        time.sleep(1)
