# We are pruning duplicate states with faster problem class (Action Compression)
# 
# To reduce dead state exploration we recusively search backwards from the targets to find all
# map positions that the box could originate from to reach each target. All boxes that are
# left untouched by this dfs search are dead states (all floor tiles dead by default)
#
# The A* basic admissible heuristic guarantees optimality and promotes the search to converge faster
#
# The A* non-basic search is not admissible and doesn't guarantee optimality but instead promotes
# fast convergence to a solution

import util
import os
import sys
import datetime
import time
import argparse
import signal
import gc
from itertools import combinations

sys.setrecursionlimit(1500)

class SokobanState:
    # player: 2-tuple representing player location (coordinates)
    # boxes: list of 2-tuples indicating box locations
    def __init__(self, player, boxes):
        # self.data stores the state
        self.data = tuple([player] + sorted(boxes))
        # below are cache variables to avoid duplicated computation
        self.all_adj_cache = None
        self.adj = {}
        self.dead = None
        self.solved = None

    def __str__(self):
        return 'player: ' + str(self.player()) + ' boxes: ' + str(self.boxes())

    def __eq__(self, other):
        return type(self) == type(other) and self.data == other.data

    def __lt__(self, other):
        return self.data < other.data

    def __hash__(self):
        return hash(self.data)
    # return player location

    def player(self):
        return self.data[0]
    # return boxes locations

    def boxes(self):
        return self.data[1:]

    def is_goal(self, problem):
        if self.solved is None:
            self.solved = all(
                problem.map[b[0]][b[1]].target for b in self.boxes())
        return self.solved

    def act(self, problem, act):
        if act in self.adj:
            return self.adj[act]
        else:
            val = problem.valid_move(self, act)
            self.adj[act] = val
            return val

    def deadp(self, problem):
        boxes = self.boxes()

        for box in boxes:
            wallInfo = {}

            for move in 'uldr':
                moveCord = parse_move(move)
                wallInfo[move] = problem.map[moveCord[0] +
                                             box[0]][moveCord[1] + box[1]].wall

            for adjMoves in ['ul', 'ld', 'dr', 'ru']:
                if(wallInfo[adjMoves[0]] and wallInfo[adjMoves[1]]):
                    if not (problem.map[box[0]][box[1]].target):
                        return True, box[0], box[1]
                else:
                    self.dead = False, None, None

        return self.dead

    def all_adj(self, problem):
        if self.all_adj_cache is None:
            succ = []
            for move in 'udlr':
                valid, box_moved, nextS = self.act(problem, move)
                if valid:
                    succ.append((move, nextS, 1))
            self.all_adj_cache = succ
        return self.all_adj_cache


class MapTile:
    def __init__(self, wall=False, floor=False, target=False, dead=False):
        self.wall = wall
        self.floor = floor
        self.target = target
        self.dead = dead

    def __str__(self):
        if self.wall:
            return "#"
        if self.target:
            return "."
        if self.dead:
            return "0"
        if self.floor:
            return " "


def parse_move(move):
    if move == 'u':
        return (-1, 0)
    elif move == 'd':
        return (1, 0)
    elif move == 'l':
        return (0, -1)
    elif move == 'r':
        return (0, 1)
    raise Exception('Invalid move character.')


class DrawObj:
    WALL = '\033[37;47m \033[0m'
    PLAYER = '\033[97;40m@\033[0m'
    BOX_OFF = '\033[30;101mX\033[0m'
    BOX_ON = '\033[30;102mX\033[0m'
    TARGET = '\033[97;40m*\033[0m'
    FLOOR = '\033[30;40m \033[0m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class SokobanProblem(util.SearchProblem):
    # valid sokoban characters
    valid_chars = 'T#@+$*. '

    def __init__(self, map, dead_detection=False, a2=False):
        self.map = [[]]
        self.temp_map = [[]]
        self.dead_detection = dead_detection
        self.init_player = (0, 0)
        self.init_boxes = []
        self.numboxes = 0
        self.targets = []
        self.visited = set()
        self.parse_map(map)
        self.gen_d_map()

        # for x in self.map:
        #     for y in x:
        #         print(y, end='')
        #     print('')

    def gen_d_map(self):
        dim = 0
        for x in self.temp_map:
            if len(x) > dim:
                dim = len(x)

        # print('dim', dim)

        self.map.insert(0, [MapTile(wall=True) for _ in range(dim + 1)])
        self.map.append([MapTile(wall=True) for _ in range(dim + 1)])
        for x in self.map:
            x.insert(0, MapTile(wall=True))
            while len(x) < dim + 2:
                x.append(MapTile(wall=True))
            # print(x)

        def dfs(xT, yT, visited):

            test1 = {}
            test2 = {}

            for move in 'udlr':
                x, y = parse_move(move)
                if (xT, yT, x + xT, y + yT) not in visited:

                    # print(f'testing ({xT},{yT}) to ({x + xT},{y + yT})')
                    test1[move] = self.map[x + xT][y + yT].floor
                    test2[move] = self.map[x*2 + xT][y*2 + yT].floor

                    visited[(xT, yT, x + xT, y + yT)] = True # visited (from, to)
                    # if you can get to it go next 
                    if test1[move] and test2[move]:
                        self.map[x + xT][y + yT].dead = False
                        # print(f'({x + xT},{y + yT}) is not dead')
                        dfs(x + xT, y + yT, visited)



        # for x in self.map:
        #     for y in x:
        #         print(y, end='')
        #     print('')

        for target in self.targets:
            xT, yT = target[0] + 1, target[1] + 1
            dfs(xT, yT, {}) #visited initially emtpy

        self.map.pop(0)
        self.map.pop(-1)
        for x in self.map:
            x.pop(0)
            x.pop(-1)

    # parse the input string into game map
    # Wall              #
    # Player            @
    # Player on target  +
    # Box               $
    # Box on target     *
    # Target            .
    # Floor             (space)

    def parse_map(self, input_str):
        def coordinates(): return (len(self.map)-1, len(self.map[-1])-1)
        for c in input_str:
            if c == '#':
                self.map[-1].append(MapTile(wall=True))
                self.temp_map[-1].append(1)
            elif c == ' ':
                self.map[-1].append(MapTile(floor=True, dead=True))
                self.temp_map[-1].append(0)
            elif c == '@':
                self.map[-1].append(MapTile(floor=True, dead=True))
                self.init_player = coordinates()
                self.temp_map[-1].append(0)
            elif c == '+':
                self.map[-1].append(MapTile(floor=True, target=True))
                self.init_player = coordinates()
                self.targets.append(coordinates())
                self.temp_map[-1].append(0)
            elif c == '$':
                self.map[-1].append(MapTile(floor=True))
                self.init_boxes.append(coordinates())
                self.temp_map[-1].append(0)
            elif c == '*':
                self.map[-1].append(MapTile(floor=True, target=True))
                self.init_boxes.append(coordinates())
                self.targets.append(coordinates())
                self.temp_map[-1].append(0)
            elif c == '.':
                self.map[-1].append(MapTile(floor=True, target=True))
                self.targets.append(coordinates())
                self.temp_map[-1].append(9)
            elif c == '\n':
                self.map.append([])
                self.temp_map.append([])

        assert len(self.init_boxes) == len(
            self.targets), 'Number of boxes must match number of targets.'
        self.numboxes = len(self.init_boxes)

    def print_state(self, s):
        for row in range(len(self.map)):
            for col in range(len(self.map[row])):
                target = self.map[row][col].target
                box = (row, col) in s.boxes()
                player = (row, col) == s.player()
                if box and target:
                    print(DrawObj.BOX_ON, end='')
                elif player and target:
                    print(DrawObj.PLAYER, end='')
                elif target:
                    print(DrawObj.TARGET, end='')
                elif box:
                    print(DrawObj.BOX_OFF, end='')
                elif player:
                    print(DrawObj.PLAYER, end='')
                elif self.map[row][col].wall:
                    print(DrawObj.WALL, end='')
                else:
                    print(DrawObj.FLOOR, end='')
            print()

    # decide if a move is valid
    # return: (whether a move is valid, whether a box is moved, the next state)
    def valid_move(self, s, move, p=None):
        if p is None:
            p = s.player()
        dx, dy = parse_move(move)
        x1 = p[0] + dx
        y1 = p[1] + dy
        x2 = x1 + dx
        y2 = y1 + dy
        if self.map[x1][y1].wall:
            return False, False, None
        elif (x1, y1) in s.boxes():
            if self.map[x2][y2].floor and (x2, y2) not in s.boxes():
                return True, True, SokobanState((x1, y1),
                                                [b if b != (x1, y1) else (x2, y2) for b in s.boxes()])
            else:
                return False, False, None
        else:
            return True, False, SokobanState((x1, y1), s.boxes())

    ##############################################################################
    # Problem 1: Dead end detection                                              #
    # Modify the function below. We are calling the deadp function for the state #
    # so the result can be cached in that state. Feel free to modify any part of #
    # the code or do something different from us.                                #
    # Our solution to this problem affects or adds approximately 50 lines of     #
    # code in the file in total. Your can vary substantially from this.          #
    ##############################################################################
    def init_dead_dict(self):
        return 1

    # detect dead end
    def dead_end(self, s):
        if not self.dead_detection:
            return False

        for xBox, yBox in s.boxes():
            if self.map[xBox][yBox].dead:
                return True

        return False

    def start(self):
        return SokobanState(self.init_player, self.init_boxes)

    def goalp(self, s):
        return s.is_goal(self)

    def expand(self, s):
        if self.dead_end(s):
            return []
        return s.all_adj(self)


class SokobanProblemFaster(SokobanProblem):
    ##############################################################################
    # Problem 2: Action compression                                              #
    # Redefine the expand function in the derived class so that it overrides the #
    # previous one. You may need to modify the solve_sokoban function as well to #
    # account for the change in the action sequence returned by the search       #
    # algorithm. Feel free to make any changes anywhere in the code.             #
    # Our solution to this problem affects or adds approximately 80 lines of     #
    # code in the file in total. Your can vary substantially from this.          #
    ##############################################################################

    # returns all possible moves of all of the boxes

    def expand(self, s):

        succ = []


        def getMoves(s):
            self.visited.add(s)
            for move in 'udlr':
                valid, box_moved, nextS = self.valid_move(s, move)
                if nextS not in self.visited and valid:
                    succ.append((move, nextS, 1))

        if self.dead_end(s):
            return []
        getMoves(s)
        # print('return succ', succ)
        return succ

    # def expand(self, s):
    #     if self.dead_end(s):
    #         return []
    #     return s.all_adj(self)


class Heuristic:
    def __init__(self, problem):
        self.problem = problem

    ##############################################################################
    # Problem 3: Simple admissible heuristic                                     #
    # Implement a simple admissible heuristic function that can be computed      #
    # quickly based on Manhattan distance. Feel free to make any changes         #
    # anywhere in the code.                                                      #
    # Our solution to this problem affects or adds approximately 10 lines of     #
    # code in the file in total. Your can vary substantially from this.          #
    ##############################################################################
    def heuristic(self, s):

        # assign boxes to targets based on the Manhattan distance
        # |x1 ??? x2| + |y1 ??? y2|

        boxes = s.boxes()

        cost = 0
        # manhattan distance matrix
        mdist = [[-1 for _ in boxes] for _ in boxes]

        for i in range(len(boxes)):
            for j in range(len(self.problem.targets)):
                xBox, yBox = boxes[i]
                xTarget, yTarget = self.problem.targets[j]
                mdist[i][j] = abs(xBox - xTarget) + abs(yBox - yTarget)
            cost += min(mdist[i])

        # for x in mdist:
        #     cost += min(x)
        #     i = x.index(min(x))
        #     for y in mdist:
        #         # print(y)
        #         y.remove(y[i])

        return cost * 2





    ##############################################################################
    # Problem 4: Better heuristic.                                               #
    # Implement a better and possibly more complicated heuristic that need not   #
    # always be admissible, but improves the search on more complicated Sokoban  #
    # levels most of the time. Feel free to make any changes anywhere in the     #
    # code. Our heuristic does some significant work at problem initialization   #
    # and caches it.                                                             #
    # Our solution to this problem affects or adds approximately 40 lines of     #
    # code in the file in total. Your can vary substantially from this.          #
    ##############################################################################
    def heuristic2(self, s):

        # ideas:
        # - prunes boxes on targets
        # - add distance from box to robot (if not on target)
        # - targets unfilled

        boxes = s.boxes()

        cost = 0
        # manhattan distance matrix
        mdist = [[-1 for _ in boxes] for _ in boxes]

        xPlayer, yPlayer = s.player()
        for i in range(len(boxes)):
            xBox, yBox = boxes[i]
            cost += abs(xBox - xPlayer) + abs(yBox - yPlayer)
            for j in range(len(self.problem.targets)):
                xTarget, yTarget = self.problem.targets[j]
                mdist[i][j] = abs(xBox - xTarget) + abs(yBox - yTarget)

        # prunes boxes that are on targets from the cost
        for x in mdist:
            if min(x) == 0:
                i = x.index(min(x))
                for y in mdist:
                    # print(y)
                    y.remove(y[i])
            else:
                cost += 10  # ! this may need a coefficient

        for x in mdist:
            if len(x) < 1:
                break
            cost += min(x)
            i = x.index(min(x))
            for y in mdist:
                # print(y)
                y.remove(y[i])

        return cost * 100


# solve sokoban map using specified algorithm
#  algorithm can be ucs a a2 fa fa2


def solve_sokoban(map, algorithm='ucs', dead_detection=False):
    # problem algorithm
    if 'f' in algorithm:
        problem = SokobanProblemFaster(map, dead_detection, '2' in algorithm)
    else:
        problem = SokobanProblem(map, dead_detection, '2' in algorithm)

    # search algorithm
    h = Heuristic(problem).heuristic2 if (
        '2' in algorithm) else Heuristic(problem).heuristic
    if 'a' in algorithm:
        search = util.AStarSearch(heuristic=h)
    else:
        search = util.UniformCostSearch()

    # solve problem
    search.solve(problem)
    if search.actions is not None:
        print('length {} soln is {}'.format(
            len(search.actions), search.actions))
    if 'f' in algorithm:
        # print('search', search.totalCost, search.actions, search.numStatesExplored)
        return search.totalCost, search.actions, search.numStatesExplored
    else:
        return search.totalCost, search.actions, search.numStatesExplored

# let the user play the map


def play_map_interactively(map, dt=0.2):

    problem = SokobanProblem(map)
    state = problem.start()
    clear = 'cls' if os.name == 'nt' else 'clear'

    seq = ""
    i = 0
    visited = [state]

    os.system(clear)
    print()
    problem.print_state(state)

    while True:
        while i > len(seq)-1:
            try:
                seq += input('enter some actions (q to quit, digit d to undo d steps ): ')
            except EOFError:
                print()
                return

        os.system(clear)
        if seq != "":
            print(seq[:i] + DrawObj.UNDERLINE +
                  seq[i] + DrawObj.END + seq[i+1:])
        problem.print_state(state)

        if seq[i] == 'q':
            return
        elif seq[i] in ['u', 'd', 'l', 'r']:
            time.sleep(dt)
            valid, _, new_state = problem.valid_move(state, seq[i])
            state = new_state if valid else state
            visited.append(state)
            os.system(clear)
            print(seq)
            problem.print_state(state)
            if not valid:
                print('Cannot move ' + seq[i] + ' in this state')
        elif seq[i].isdigit():
            i = max(-1, i - 1 - int(seq[i]))
            seq = seq[:i+1]
            visited = visited[:i+2]
            state = visited[i+1]
            os.system(clear)
            print(seq)
            problem.print_state(state)

        if state.is_goal(problem):
            for _ in range(10):
                print('\033[30;101mWIN!!!!!\033[0m')
            time.sleep(5)
            return
        i = i + 1

# animate the sequence of actions in sokoban map


def animate_sokoban_solution(map, seq, dt=0.2):
    problem = SokobanProblem(map)
    state = problem.start()
    clear = 'cls' if os.name == 'nt' else 'clear'
    for i in range(len(seq)):
        os.system(clear)
        print(seq[:i] + DrawObj.UNDERLINE + seq[i] + DrawObj.END + seq[i+1:])
        problem.print_state(state)
        time.sleep(dt)
        valid, _, state = problem.valid_move(state, seq[i])
        if not valid:
            raise Exception('Cannot move ' +
                            seq[i] + ' in state ' + str(state))
    os.system(clear)
    print(seq)
    problem.print_state(state)

# read level map from file, returns map represented as string


def read_map_from_file(file, level):
    map = ''
    start = False
    found = False
    with open(file, 'r') as f:
        for line in f:
            if line[0] == "'":
                continue
            if line.strip().lower()[:5] == 'level':
                if start:
                    break
                if line.strip().lower() == 'level ' + level:
                    found = True
                    start = True
                    continue
            if start:
                if line[0] in SokobanProblem.valid_chars:
                    map += line
                else:
                    break
    if not found:
        raise Exception('Level ' + level + ' not found')
    return map.strip('\n')

# extract all levels from file


def extract_levels(file):
    levels = []
    with open(file, 'r') as f:
        for line in f:
            if line.strip().lower()[:5] == 'level':
                levels += [line.strip().lower()[6:]]
    return levels


def extract_timeout(file, level):
    start = False
    found = False
    with open(file, 'r') as f:
        for line in f:
            if line[0] == "'":
                continue
            if line.strip().lower()[:5] == 'level':
                if start:
                    break
                if line.strip().lower() == 'level ' + level:
                    found = True
                    continue
            if found:
                if line.strip().lower()[:7] == 'timeout':
                    return(int(line.strip().lower()[8:]))
                else:
                    break
    if not found:
        raise Exception('Level ' + level + ' not found')
    return None


def solve_map(file, level, algorithm, dead, simulate):
    map = read_map_from_file(file, level)
    print(map)
    if dead:
        print(
            'Dead end detection on for solution of level {level}'.format(**locals()))
    if algorithm == "me":
        play_map_interactively(map)
    else:
        tic = datetime.datetime.now()
        cost, sol, nstates = solve_sokoban(map, algorithm, dead)
        toc = datetime.datetime.now()
        print('Time consumed: {:.3f} seconds using {} and exploring {} states'.format(
            (toc - tic).seconds + (toc - tic).microseconds/1e6, algorithm, nstates))
        seq = ''.join(sol)
        print(len(seq), 'moves')
        print(' '.join(seq[i:i+5] for i in range(0, len(seq), 5)))
        if simulate:
            animate_sokoban_solution(map, seq)
        return (toc - tic).seconds + (toc - tic).microseconds/1e6


def main():
    parser = argparse.ArgumentParser(description="Solve Sokoban map")
    parser.add_argument("level", help="Level name or 'all'")
    parser.add_argument("algorithm", help="me | ucs | [f][a[2]] | all")
    parser.add_argument(
        "-d", "--dead", help="Turn on dead state detection (default off)", action="store_true")
    parser.add_argument(
        "-s", "--simulate", help="Simulate the solution (default off)", action="store_true")
    parser.add_argument(
        "-f", "--file", help="File name storing the levels (levels.txt default)", default='levels.txt')
    parser.add_argument(
        "-t", "--timeout", help="Seconds to allow (default 300) (ignored if level specifies)", type=int, default=300)

    args = parser.parse_args()
    level = args.level
    algorithm = args.algorithm
    dead = args.dead
    simulate = args.simulate
    file = args.file
    maxSeconds = args.timeout

    if (algorithm == 'all' and level == 'all'):
        raise Exception('Cannot do all levels with all algorithms')

    def solve_now(): return solve_map(file, level, algorithm, dead, simulate)

    def solve_with_timeout(timeout):
        level_timeout = extract_timeout(file, level)
        if level_timeout != None:
            timeout = level_timeout

        try:
            return util.TimeoutFunction(solve_now, timeout)()
        except KeyboardInterrupt:
            raise
        except MemoryError as e:
            signal.alarm(0)
            gc.collect()
            print('Memory limit exceeded.')
            return None
        except util.TimeoutFunctionException as e:
            signal.alarm(0)
            print('Time limit (%s seconds) exceeded.' % timeout)
            return None

    if level == 'all':
        levels = extract_levels(file)
        solved = 0
        time_used = 0
        for level in levels:
            print('Starting level {}'.format(level), file=sys.stderr)
            sys.stdout.flush()
            result = solve_with_timeout(maxSeconds)
            if result != None:
                solved += 1
                time_used += result
        print(
            f'\n\nOVERALL RESULT: {solved} levels solved out of {len(levels)} ({100.0*solved/len(levels)})% using {time_used:.3f} seconds')
    elif algorithm == 'all':
        for algorithm in ['ucs', 'a', 'a2', 'f', 'fa', 'fa2']:
            print('Starting algorithm {}'.format(algorithm), file=sys.stderr)
            sys.stdout.flush()
            solve_with_timeout(maxSeconds)
    elif algorithm == 'me':
        solve_now()
    else:
        solve_with_timeout(maxSeconds)


if __name__ == '__main__':
    main()
