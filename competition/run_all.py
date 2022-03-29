import argparse
import subprocess
import os
from datetime import datetime as dt

def main():

    parser = argparse.ArgumentParser(description="Compare sokoban algorithms")
    parser.add_argument("-f", "--file", help="levels file name", default='levels.txt')
    parser.add_argument("-p", "--python_solver_source", default='sokoban.py')
    parser.add_argument("-t", "--timeout", help="Seconds to allow (default 300) (ignored if level specifies)", type=int, default=300)
    parser.add_argument("-l", "--level", help="level to solve", default='all')
    args = parser.parse_args()
    level_file = args.file
    timeout = args.timeout
    solution_code = args.python_solver_source
    level = args.level

    to_compare = [('fa2',True), ('a2',True), ('fa',True), ('f',True), ('ucs',True), ('ucs',False)] # (algorithm string, Boolean for deadend detection or not)
#    to_compare = [('a2',True)]
    results=''
    for alg, dead_end in to_compare:
        dead_end_option = '-d' if dead_end else '' 
        log_file_name = level_file+"-log-" + alg + dead_end_option + ".log"
        with open(log_file_name, "w") as f:
            command = "python3 %s %s %s %s -f %s -t %s" % (solution_code, level, alg, dead_end_option, level_file, timeout)
            print(f'executing {command}')
            subprocess.call(command, stderr=f, stdout=f, shell=True)
        with open(log_file_name, "r") as f:
            for line in f:
                if line.strip().lower()[:5] == 'overa':
                    results += f'    Algorithm {alg} {dead_end_option} gives ' + line
    with open(level_file+' summary_of_run.txt',"a") as f:
        n=dt.now()
        print(n.strftime("%x %X")+f' Levels from {level_file} gave:')
        print(results,file=f)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Exception thrown:')
        print(e)
