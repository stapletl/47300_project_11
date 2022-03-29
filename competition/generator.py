import argparse, os
import sys
import random
import time
import math
import datetime
from collections import deque

def print_debug(s) :
    pass
    #print(s)

def millitime() :
    return int(round(time.time() * 1000))

w_count_coef = 0.0
g_count_coef = 0.0
b_count_coef = 0.0

stat_explore_count = 0
stat_exploit_count = 0
stat_explore_window_len = 50000
stat_explore_queue = deque([1] * stat_explore_window_len)
stat_depth = 0
last_found_time = -1

floor = 0
wall = 1
goal = 2
directions = [(0,-1), (1, 0), (0, 1), (-1, 0)]

def move_pos(pos, dir) :
    return (pos[0] + dir[0], pos[1] + dir[1])
def opposite_dir(dir) :
    return (-dir[0], -dir[1])

class Cursor :
    def __init__(self, width,
                 height,
                 walls = None,
                 floors = set(),
                 boxes = [],
                 goals = [],
#                 box_paths = [],
                 box_move_count = [],
                 player_reach = set(),
                 score = 0.0,
                 terrain = 0.0,
                 w_count = 0,
                 g_count = 0,
                 b_count = 0,
                 path_crosses = 0,
                 evaluated = False,
                 next_actions = None,
                 move_sequence = [],
                 depth = 0):
        self.width = width
        self.height = height
        #        self.tiles = []
        if walls == None :
            self.walls = set()
            for j in range(height) :
                for i in range(width) :
                    self.walls.add((i,j))
        else :
            self.walls = walls

        now = datetime.datetime.now()
        self.level_name = str(width) + "_" + str(height) + "_" + str(now.year) + str(now.month) + str(now.day) + "_" + str(now.hour) + str(now.minute) + str(now.second)

        self.floors = floors
        self.boxes = boxes
        self.goals = goals
#        self.box_paths = box_paths
        self.box_move_count = box_move_count
        self.player_reach = player_reach
        self.score = score
        self.terrain = terrain
        self.w_count = w_count
        self.g_count = g_count
        self.b_count = b_count
        self.path_crosses = path_crosses
        self.evaluated = evaluated
        self.move_sequence = move_sequence
        self.depth = depth
        if next_actions == None :
            self.next_actions = set()
            init_floor = (random.randint(0, width-1), random.randint(0, height-1))
            self.next_actions.add(PlaceFloor(init_floor))
        else :
            self.next_actions = next_actions

    def clone(self) :
#        new_bpaths = []
#        for path in self.box_paths :
#            new_bpaths.append(path[:])
        clone = Cursor(self.width,
                       self.height,
                       set(self.walls),
                       set(self.floors),
                       self.boxes[:],
                       self.goals[:],
 #                     new_bpaths,
                       self.box_move_count[:],
                       set(self.player_reach),
                       self.score,
                       terrain = self.terrain,
                       w_count = self.w_count,
                       g_count = self.g_count,
                       b_count = self.b_count,
                       path_crosses = self.path_crosses,
                       evaluated = self.evaluated,
                       next_actions = set(self.next_actions),
                       move_sequence = self.move_sequence[:],
                       depth = self.depth)
        clone.level_name = self.level_name
        return clone

    def cleanup_board(self) :
        clone = self.clone()
        if len(clone.player_reach) == 0 :
            return self
        new_walls = set(clone.walls)
        new_boxes = []
        new_goals = []
        new_move_counts = []
#        new_paths = []
        for bindex in range(len(clone.boxes)) :
            if clone.box_move_count[bindex] > 0 :
#            if len(clone.box_paths[bindex]) > 1 :
                new_boxes.append(clone.boxes[bindex])
                new_goals.append(clone.goals[bindex])
                new_move_counts.append(clone.box_move_count[bindex])
#                new_paths.append(clone.box_paths[bindex][:])
            else :
                new_walls.add(clone.boxes[bindex])
        clone.boxes = []
        pos = clone.player_reach.pop()
        new_reach = set([pos])
        queue = [pos]
        while len(queue) > 0 :
            next_pos = queue.pop()
            for dir in directions :
                neigh = move_pos(next_pos, dir)
                if (not neigh in new_walls) and (clone.test_pos(neigh)) and (not neigh in new_reach) :
                    queue.append(neigh)
                    new_reach.add(neigh)

        new_floors = set(new_reach)
        new_walls.update(clone.floors - new_floors)

        new_floors = clone.floors - new_walls

        clone.walls = new_walls
        clone.floors = new_floors
        clone.boxes = new_boxes
        clone.goals = new_goals
        clone.box_move_count = new_move_counts
#        clone.box_paths = new_paths
        clone.player_reach = clone.get_reach_from(pos)

        return clone

    def test_pos(self, pos) :
        b = (pos[0] >= 0
                and pos[0] < self.width
                and pos[1] >= 0
                and pos[1] < self.height)
        return b
    def pos_to_index(self, pos) :
        return pos[1] * self.width + pos[0]
    def index_to_pos(self, index) :
        return (index % self.width, int(index / self.width))


    def place_floor(self, pos) :
        if self.test_pos(pos) :

            self.floors.add(pos)
            self.walls.discard(pos)
            self.next_actions.add(PlaceBox(pos))
            self.next_actions.add(PlacePlayer(pos))

            for dir in directions :
                new_pos = move_pos(pos, dir);

#                if new_pos in self.floors :
#                    self.terrain -= 1
#                else:
#                    if self.test_pos(new_pos) and not new_pos in self.boxes:
#                        self.next_actions.add(PlaceFloor(new_pos))
#                    self.terrain += 1

                if not new_pos in self.floors :
                    if self.test_pos(new_pos) and not new_pos in self.boxes :
                        self.next_actions.add(PlaceFloor(new_pos))
                    self.terrain += 1
                else:
                    self.terrain -= 1


# NOTE: Replace else with this to not count boxes in terrain metric
#                elif new_pos in self.floors:
#                    self.terrain -= 1

        else :
            raise ValueError("Cannot place floor here : " + str(pos))

    def place_box(self, pos) :
        if self.test_pos(pos) :
            self.boxes.append(pos)
#            self.box_paths.append([pos])
            self.box_move_count.append(0)
            self.floors.discard(pos)

# NOTE: Add back to not count boxes in terrain metric
            for dir in directions :
                neigh = move_pos(pos, dir)
                if not neigh in self.floors :
                    self.terrain -= 1
                else:
                    self.terrain += 1
#                if neigh in self.floors :
#                    self.terrain += 1
#                else:
#                    self.terrain -= 1
#                if neigh in self.walls or not self.test_pos(neigh) :
#                    self.terrain -= 1

            self.next_actions.discard(PlacePlayer(pos))

        else:
            raise ValueError("Cannot place box here : " + str(pos))

    def get_reach_from(self, pos) :
        reach = set([pos])
        queue = [pos]
        while len(queue) > 0 :
            next_pos = queue.pop()
            for dir in directions :
                neigh = move_pos(next_pos, dir)
                if neigh in self.floors and not neigh in reach :
                    queue.append(neigh)
                    reach.add(neigh)
        return reach

    def place_player(self, pos) :
        if self.test_pos(pos) :
            self.player_reach = self.get_reach_from(pos)
            self.goals = self.boxes[:]
            self.next_actions.clear()
            self.next_actions.add(Evaluate())

            bindex = 0
            for bpos in self.boxes :
                for dir in directions :
                    next_bpos = move_pos(bpos, dir)
                    next_ppos = move_pos(next_bpos, dir)
                    if next_bpos in self.floors and next_ppos in self.floors :
                        self.next_actions.add(MoveBox(bindex, dir))
                bindex += 1

        else:
            raise ValueError("Cannot place player here : " + str(pos))

    # Assuming that all these methods are called with valid arguments, btw
    def move_box(self, index, direction) :
        # Assuming that index is not out of bounds
        old_bpos = self.boxes[index]
        self.floors.add(old_bpos)
        bpos = move_pos(old_bpos, direction)
        self.floors.discard(bpos)
        self.boxes[index] = bpos
        self.player_reach = self.get_reach_from(move_pos(bpos, direction))
        self.move_sequence.append(MoveBox(index, direction))

#        pindex = 0
#        for path in self.box_paths :
#            if pindex != index and bpos in path :
#                self.path_crosses += 1
#            pindex += 1

#        self.box_paths[index].append(bpos)

        if self.box_move_count[index] == 0 :
            for dir in directions :
                neigh = move_pos(old_bpos, dir)
                is_wall = False
                if neigh in self.boxes and neigh != bpos :
                    neigh_index = self.boxes.index(neigh)
                    if self.box_move_count[neigh_index] == 0 :
                        is_wall = True

#                print(neigh, self.terrain, is_wall)

                if neigh in self.walls or is_wall or not self.test_pos(neigh) :
#                    print("+1")
                    self.terrain += 1
                else:
#                    print("-1")
                    self.terrain -= 1
#                print(self.terrain)

        self.box_move_count[index] += 1


# NOTE: add back to not count box positions in terrain metric
#        for dir in directions :
#            old_neigh = move_pos(old_bpos, dir)
#            new_neigh = move_pos(bpos, dir)
#            if old_neigh in self.walls or not self.test_pos(old_neigh) :
#                self.terrain += 1
#            if new_neigh in self.walls or not self.test_pos(new_neigh) :
#                self.terrain -= 1

        # TODO : need to decrement them too when a box moves back
#        gpos = self.goals[index]
#        x = gpos[0] if (direction[0] == 0) else old_bpos[0]
#        y = gpos[1] if (direction[1] == 0) else old_bpos[1]
#        (minx, maxx) = (min(x, bpos[0]), max(x, bpos[0]))
#        (miny, maxy) = (min(y, bpos[1]), max(y, bpos[1]))
#        for j in range(miny, maxy) :
#            for i in range(minx, maxx) :
#                if (i, j) in self.walls :
#                    self.w_count += 1
#                if (i,j) in self.boxes :
#                    bindex = self.boxes.index((i,j))
#                    if self.goals[bindex] == (i,j) :
#                        self.w_count += 1
#                        continue
#                    self.b_count += 1
#                if (i,j) in self.goals :
#                    self.g_count += 1

        bindex = 0
        for bpos in self.boxes :
            for dir in directions :
                next_bpos = move_pos(bpos, dir)
                next_ppos = move_pos(next_bpos, dir)
                if next_bpos in self.player_reach and next_ppos in self.player_reach :
                    self.next_actions.add(MoveBox(bindex, dir))
                else:
                    self.next_actions.discard(MoveBox(bindex, dir))
            bindex += 1


    def refresh_score(self) :
        index = 0
        self.w_count = 0
        self.b_count = 0
        self.g_count = 0

        manhattan = 0

#        box_neighs = len(self.goals) * 4
        box_neighs = 0
        goal_neighs = 0
        wall_neigh_change = 0

        test_trn = 0

        cleaned_self = self.cleanup_board()

        for i in range(cleaned_self.width) :
            for j in range(cleaned_self.height) :
                if not (i,j) in cleaned_self.walls :
#                if (i,j) in cleaned_self.floors or (i,j) in cleaned_self.boxes or (i,j) in cleaned_self.goals :
                    if (i,j) in cleaned_self.boxes :
                        ij_index = cleaned_self.boxes.index((i,j))
                        if cleaned_self.box_move_count[ij_index] == 0 :
                            continue
                    for dir in directions :
                        ij_neigh = move_pos((i,j), dir)
                        if ij_neigh in cleaned_self.walls or (not cleaned_self.test_pos(ij_neigh)) or (ij_neigh in cleaned_self.boxes and cleaned_self.box_move_count[cleaned_self.boxes.index(ij_neigh)] == 0) :
                            test_trn += 1


        for gpos in self.goals :
            bpos = self.boxes[index]

            index += 1
            (minx, maxx) = (min(bpos[0], gpos[0]), max(bpos[0], gpos[0]))
            (miny, maxy) = (min(bpos[1], gpos[1]), max(bpos[1], gpos[1]))
            manhattan += abs(bpos[0] - gpos[0]) + abs(bpos[1] - gpos[1])
            if bpos[0] == gpos[0] and bpos[1] == gpos[1] :
                continue
#            if minx == maxx or miny == maxy :
#                continue

            goal_neighs += 4

            for dir in directions :
                bneigh = move_pos(bpos, dir)
#                if bneigh in self.walls or not self.test_pos(bneigh) :
#                    box_neighs += 1
                gneigh = move_pos(gpos, dir)
#                if gneigh in self.walls or not self.test_pos(gneigh) :
#                    goal_neighs -= 1
                test_bneigh = bneigh in self.walls or not self.test_pos(bneigh)
                test_gneigh = gneigh in self.walls or not self.test_pos(gneigh)
                if test_bneigh and not test_gneigh :
                    wall_neigh_change += 1

            for y in range(miny, maxy + 1) :
                for x in range(minx, maxx + 1) :
                    if (x, y) in self.walls :
                        self.w_count += 1
                    if (x, y) in self.boxes :
                        bindex = self.boxes.index((x,y))
                        if self.box_move_count[bindex] == 0 :
#                        if len(self.box_paths[bindex]) <= 1 :
                            self.w_count += 1
                            continue
                        self.b_count += 1
                    if (x, y) in self.goals :
                        self.g_count += 1
            self.g_count -= 1
            self.b_count -= 1

        self.g_count = max(0, self.g_count)
        self.b_count = max(0, self.b_count)

        efficiency = 1000.0 / (1000.0 + len(self.move_sequence))
        efficiency = math.log(len(self.move_sequence) + 1)
        efficiency = math.sqrt(len(self.move_sequence))

        global w_count_coef
        global b_count_coef
        global g_count_coef

        congestion = (  w_count_coef * (self.w_count + 0.5)
                      + g_count_coef * (self.g_count + 0.5)
                      + b_count_coef * (self.b_count + 0.5)) # / max(len(self.boxes), 1.0)

        congestion = max(congestion, 0.0001)


#        dispatching = abs(self.g_count - self.b_count) + 0.5


#        crossings = (self.path_crosses)
#        crossings = math.log(self.path_crosses + 1)
#        crossings = math.sqrt(self.path_crosses)
#        crossings = math.sqrt(self.path_crosses)n
#        crossings = (self.path_crosses)

#        if self.terrain != test_trn :
#            print(self.string_rep())
#            print(test_trn)
#            input()

        if (self.terrain < 0) :
            print(self)
            print("terrain negative!")
            input("!!")

#        if (len(self.floors) > 0) :
#            terr = self.terrain / (10.0 + len(self.floors))
#        else :
#            terr = self.terrain

        trn = self.terrain / (1.0 * (self.width * self.height - len(self.walls)) + 1)
        trn = self.terrain
        trn = test_trn
#        trn = self.terrain / (1.0 + len(self.floors))

        self.score = (((efficiency ** 0.0) * (wall_neigh_change ** 1.0) * congestion * trn) ** (1.0/3.0)) * 0.6
#        self.score = (((efficiency ** 0.0) * crossings * trn) ** (1.0/2.0)) * 2.5
#        self.score = ((manhattan + (efficiency ** 0.0) * congestion * trn) ** (1.0/3.0)) / 2.0
#        self.score = math.sqrt(congestion * self.terrain) / 2.0

    def hash(self) :
        return hash((self.width, frozenset(self.walls), tuple(self.boxes), tuple(self.goals), frozenset(self.player_reach), self.evaluated))

    def evaluate(self) :
        self.evaluated = True
        #self.hsh = hash((self.hsh, "evaluated"))
        #self.refresh_score()
        self.next_actions.clear()


    def simulate(self) : # TODO find a way to use visited
        pass#print_debug(">> simulate()")
        while len(self.next_actions) > 0 :
            #pass#print_debug("next_actions.count : " + str(len(self.next_actions)))
            #s = ""
            #for action in self.next_actions :
            #    s += str(action) + ", "
            #pass#print_debug(s)
            action = random.sample(self.next_actions, 1)[0]
            pass#print_debug("   ... simulate " + str(action))
            #input()
            action.update_cursor(self)

        pass#print_debug("   ... Simulated cursor :\n" + str(self))

    def __eq__(self, other) :
        return isinstance(other, Cursor) and self.hash() == other.hash()

    def cleaned_up_str(self) :
        cleaned = self.cleanup_board()
        if cleaned :
            return str(cleaned.string_rep())

    def __str__(self) :
        s = "Level " + self.level_name + "\n"
        player = random.randint(0,len(self.player_reach)-1)
        for j in range(self.height) :
            for i in range(self.width) :
                if (i,j) in self.walls :
                    s += "#"
                if ((i,j) in self.goals
                    and (i, j) in self.boxes) :
                    s += "*"
                elif (i,j) in self.goals :
                    s += "."
                elif (i,j) in self.boxes :
                    s += "$"
                elif (i,j) in self.player_reach :
                    s += "@" if player==0 else " "
                    player -= 1
                elif (i,j) in self.floors :
                    s += " "
            s += "\n"
        # s += "w, g, b : " + str((self.w_count, self.g_count, self.b_count)) + "\n"
        # s += "path_xs : " + str(self.path_crosses) + "\n"
        # s += "terrain : " + str(self.terrain) + "\n"
        # s += "score   : " + str(self.score) + "\n"
        # s += "eval    : " + str(self.evaluated) + "\n"
        # s += "hash    : " + str(self.hash()) + "\n"
        # s += "moves   : " + str(len(self.move_sequence)) + "\n"
        # s += "goals   : " + str(list(self.goals)) + "\n"
        # s += "next_actions.count : " + str(len(self.next_actions)) + "\n"
        # s += "next_actions : " + str(self.next_actions)
        return s

    def string_rep(self) :
        s = "Level " + self.level_name + "\n"
        if len(self.player_reach) <=0 :
        #     pp = self.player_reach.pop()
        #     self.player_reach.add(pp)
        #     s += str(pp[0]) + "," + str(pp[1]) + "\n"
        # else :
            s += "> Invalid; no player\n"
        player = random.randint(0,len(self.player_reach)-1)
        debug = player
        for j in range(self.height) :
            for i in range(self.width) :
                if (i,j) in self.walls :
                    s += "#"
                elif ((i,j) in self.goals
                      and (i,j) in self.boxes) :
                    bindex = self.boxes.index((i,j))
                    if self.box_move_count[bindex] == 0 :
#                    if len(self.box_paths[bindex]) <= 1 :
                        s += "*"
                    else:
                        s += "*"
                elif (i,j) in self.goals :
                    if (i,j) in self.player_reach:
                        s += "+" if player==0 else "."
                        player -= 1
                    else:
                        s += "."
                elif (i,j) in self.boxes :
                    s += "$"
                elif (i,j) in self.player_reach :
                    s += "@" if player==0 else " "
                    player -= 1
                elif (i,j) in self.floors :
                    s += " "
                else :
                    s += "#"
            s += "\n"
        # s += "> score   : " + str(self.score) + "\n"
        # s += "> w, g, b : " + str((self.w_count, self.g_count, self.b_count)) + "\n"
        # s += "> path_xs : " + str(self.path_crosses) + "\n"
        # s += "> terrain : " + str(self.terrain) + "\n"
        # s += "> hash    : " + str(self.hash()) + "\n"
        # s += "> pushes  : " + str(len(self.move_sequence)) + "\n"
        # s += "> depth   : " + str(self.depth) + "\n"
        # s += ">\n"
        if player >= 0:
            print(f'stringrep failure with len(self.player_reach) = {len(self.player_reach)} debug = {debug} player = {player}')
            print(f'self.player_reach = {self.player_reach}')
            print(f'computed string rep is:\n{s}\n\n' )
        return s

class PlaceFloor :
    def __init__(self, pos) :
        self.pos = pos
    def update_cursor(self, cursor) :
        cursor.next_actions.discard(self)
        cursor.place_floor(self.pos)
        cursor.depth += 1
    def __eq__(self, other):
        return isinstance(other, PlaceFloor) and other.pos == self.pos
    def __hash__(self) :
        return hash((0, self.pos));
    def __str__(self) :
        return self.__class__.__name__ + "[" + str(self.pos) + "]";
class PlaceBox :
    def __init__(self, pos) :
        self.pos = pos
    def update_cursor(self, cursor) :
        cursor.next_actions.discard(self)
        cursor.place_box(self.pos)
        cursor.depth += 1
    def __eq__(self, other):
        return isinstance(other, PlaceBox) and other.pos == self.pos
    def __hash__(self) :
        return hash((1, self.pos));
    def __str__(self) :
        return self.__class__.__name__ + "[" + str(self.pos) + "]";
class PlacePlayer :
    def __init__(self, pos) :
        self.pos = pos
    def update_cursor(self, cursor) :
        cursor.place_player(self.pos)
        cursor.depth += 1
    def __eq__(self, other):
        return isinstance(other, PlacePlayer) and other.pos == self.pos
    def __hash__(self) :
        return hash((2, self.pos));
    def __str__(self) :
        return self.__class__.__name__ + "[" + str(self.pos) + "]";
class MoveBox :
    def __init__(self, index, direction) :
        self.index = index
        self.direction = direction
    def update_cursor(self, cursor) :
        cursor.move_box (self.index, self.direction)
        cursor.depth += 1
    def __eq__(self, other):
        return isinstance(other, MoveBox) and other.index == self.index and other.direction == self.direction
    def __hash__(self) :
        return hash((3, self.index, self.direction));
    def __str__(self) :
        return "MoveBox[" + str(self.index) + ", towards " + str(self.direction) + "]"
class Evaluate :
    def __init__(self) :
        pass
    def update_cursor(self, cursor) :
        cursor.evaluate()
        cursor.depth += 1
    def __eq__(self, other):
        return isinstance(other, Evaluate)
    def __hash__(self) :
        return hash(4);
    def __str__(self) :
        return "Evaluate";

class Node :
    def __init__(self, parent, last_action, cursor) :
        self.parent = parent
        self.children = []
        self.last_action = last_action
        self.visited_count = 1
        self.score = 0.0
        self.average_score = 0.0
        self.cached_cursor = cursor.clone()

    def select(self) :
        pass#print_debug(">> select()")
        node = self
        while len(node.children) > 0 :
            max_ucb = 0.0
            max_node = node.children[0]
            max_score = 0.0
            max_score_node = node.children[0]
            for c in node.children :
                c_ucb = c.ucb()
                if c_ucb > max_ucb :
                    max_ucb = c_ucb
                    max_node = c
                c_score = c.average_score
                if c_score > max_score :
                    max_score = c_score
                    max_score_node = c
            node = max_node
            global stat_explore_queue
            if max_score == max_node.average_score :
                global stat_exploit_count
                stat_exploit_count += 1
                stat_explore_queue.append(0)
            else:
                global stat_explore_count
                stat_explore_count += 1
                stat_explore_queue.append(1)
            stat_explore_queue.popleft()
            pass#print_debug("   ... select : " + str(node.last_action))
        return node

    # Assumes that self has not yet been expanded, i.e. that self.children is empty
    def expand(self, visited_hashes) :
        for action in self.cached_cursor.next_actions :
            cursor_clone = self.cached_cursor.clone()
            action.update_cursor(cursor_clone)
            cc_hash = cursor_clone.hash()
            if not cc_hash in visited_hashes :
                child_node = Node(self, action, cursor_clone)
                self.children.append(child_node)
                visited_hashes.add(cc_hash)
            else:
                pass#print_debug("cursor already visited for action " + str(action))
                pass
        pass#print_debug(">> expand() : " + str(len(self.children)) + " new children")

    def random_child(self) :
        if len(self.children) > 0 :
            return self.children[random.randint(0, len(self.children)-1)]
        else :
            return None

    def remove_child(self, child) :
        self.children.remove(child) # NOTE dangerous. can throw if child not in children
        pass#print_debug("remove_child")

    def remove_from_parent(self) :
        if self.parent != None :
            self.parent.remove_child(self)

    def ucb(self, verbose = False) :
        parent = self.parent
        if parent != None :
            explore = 1 * math.sqrt((2.0 + math.log(parent.visited_count)) / self.visited_count)
            if (verbose) :
                print("ucb - exploration : " + str(explore) + ", exploitation : " + str(self.average_score))
            return (self.average_score + explore)
        else:
            return self.average_score

    def backpropagate(self, from_cursor) :
        pass#print_debug(">> backpropagate")
        node = self
        src_score = from_cursor.score
        while node != None :
            node.visited_count += 1
            node.score += src_score
            node.average_score = node.score / node.visited_count
            parent = node.parent
            node = parent

    def __str__(self) :
        s = "Node\n"
        s += "children.count : " + str(len(self.children)) + "\n"
        s += "last_action    : " + str(self.last_action) + "\n"
        s += "score          : " + str(self.score) + "\n"
        s += "visited_count  : " + str(self.visited_count) + "\n"
        s += "average_score  : " + str(self.average_score) + "\n"
        s += "ucb            : " + str(self.ucb) + "\n"
        s += "Cached Cursor :\n" + str(self.cached_cursor)
        return s


def mcts(minsize, maxsize, dir) :
    seed = millitime()
    random.seed(seed)

    visited_hashes = set()

    global w_count_coef
    global g_count_coef
    global b_count_coef

    w_count_coef = random.uniform(-0.3, 1.0)
    g_count_coef = random.uniform(-0.3, 1.0)
    b_count_coef = random.uniform(-0.3, 1.0)

    w_count_coef = 0.4
    g_count_coef = 0.25
    b_count_coef = 1.0

    max_coef = max(max(w_count_coef, b_count_coef), g_count_coef)
    min_coef = 0.1
    if max_coef <= min_coef :
        w_count_coef += abs(max_coef) + min_coef
        b_count_coef += abs(max_coef) + min_coef
        g_count_coef += abs(max_coef) + min_coef

#    width, height = random.randint(5,9), random.randint(5,9)
    width, height = random.randint(minsize,maxsize), random.randint(minsize,maxsize)
    cursor = Cursor(width, height)
    root = Node(None, None, cursor)

    best_cursor = cursor
    best_score = -1.0

    #selected = root.select()
    #print(root)
    #print("\nSelected :\n" + str(selected))
    #selected.expand(visited_hashes)
    #print("\nSelected after expansion :\n" + str(selected))
    #child = selected.random_child()
    #print("\nRandom child from selected :\n" + str(child))
    #print("\nSimulating...\n")
    #child_cursor = child.cached_cursor.clone()
    #child_cursor.simulate()
    #print("\nSimulated cursor :\n" + str(child_cursor))

    start_time = millitime()
    iter_count = 0
    now = datetime.datetime.now()
    found_iter = 0
#        f.write("> Width : " + str(width) + "\n")
#        f.write("> Height : " + str(height) + "\n")
#        f.write("> Seed : " + str(seed) + "\n")
#        f.write(">\n>\n")
    while (millitime() - start_time < 1000 * 60 * 30) :
        selected = root.select()
        selected.expand(visited_hashes)
        for i in range(15) :
            child = selected.random_child()
            if child == None :
                simulated = selected.cached_cursor
                simulated.refresh_score()
                selected.backpropagate(simulated)
                selected.remove_from_parent()
                break
            else:
                simulated = child.cached_cursor.clone()
                simulated.simulate()
                simulated.refresh_score()
                child.backpropagate(simulated)

            global stat_depth
            if simulated.depth > stat_depth :
                stat_depth = simulated.depth

            if simulated.score > best_score :
                best_score = simulated.score
                best_cursor = simulated
                print("\nVisited puzzles : " + str(len(visited_hashes)))
                print("w_count " + str(w_count_coef) + "\ng_count " + str(g_count_coef) + "\nb_count " + str(b_count_coef))
                print("Best Cursor yet with score " + str(best_score) + " :\n" + str(best_cursor.cleaned_up_str()))
                print("\a")
                found_iter  = iter_count
                global last_found_time
                last_found_time = millitime()
    #            f.write(best_cursor.string_rep())
    #            f.write("> Iteration " + str(iter_count) + "\n")
    #            f.write("\n***")

            if (iter_count % 250 == 0) :
                duration = int((millitime() - start_time) / 1000)
                seconds = duration % 60
                minutes = int(duration / 60)
                dots_count = int((iter_count % 5000) / 250)
                global stat_explore_queue
                explore_avg = sum(stat_explore_queue) / (stat_explore_window_len)
                sys.stdout.write("\riteration " + str(iter_count) + " (" + str(minutes) + "m " + str(seconds) + "s) depth : " + str(stat_depth) + " \texplore/exploit : "+str(stat_explore_count) + "/" + str(stat_exploit_count + 1)+" = " + str(stat_explore_count/(stat_exploit_count + 1)) + " \texplore/iteration : " + str(stat_explore_count/(iter_count + 1)) + ", \t" + str(explore_avg) + (dots_count * ".") + ((50 - dots_count) * " ") + "\r")
                #if (iter_count % 5000 == 0):
                    #input()
#                print(simulated.string_rep())
#                input()

            iter_count += 1

        giveup_minutes = 5
        if (millitime() - last_found_time) > 1000 * 60 * giveup_minutes :
            print("Did not find anything better in " + str(giveup_minutes))
            break

#        child = selected.random_child()
#        if child == None :
#            simulated = selected.cached_cursor
#            simulated.refresh_score()
#            selected.backpropagate(simulated)
#            selected.remove_from_parent()
#        else:
#            simulated = child.cached_cursor.clone()
#            simulated.simulate()
#            simulated.refresh_score()
#            child.backpropagate(simulated)

#    walled_cursor = wall_around_board(best_cursor)
#    print(best_cursor.cleaned_up_str())
#    print(walled_cursor.string_rep())
#    return

    rep = wall_around_board(best_cursor).string_rep()
    if not ('@' in rep or '+' in rep) :  # a debugging check, hopefully won't trigger
        print(f'Failure to situate player, with cursor.player_reach = {best_cursor.player_reach}')
        print('Proposed level is')
        print(wall_around_board(best_cursor).string_rep())
        return False
    else:
        with open(f"{dir}/level_" + cursor.level_name + ".soko", 'a') as f :
            f.write(rep)
            f.write("\n")
            # f.write("> w_count " + str(w_count_coef) + "\n> g_count " + str(g_count_coef) + "\n> b_count " + str(b_count_coef))
            # f.write("\n> Iteration " + str(found_iter) + "/" + str(iter_count) + "\n")
            # f.write("\n***")
        return True

def wall_around_board(cursor) :
    cursor = cursor.cleanup_board()
    changes = [1,1,1,1]
    rows = []
    columns = [True] * cursor.width
    print(cursor.walls)
    for j in range(cursor.height) :
        rows.append(True)
        for i in range(cursor.width) :
            if not (i,j) in cursor.walls :
                print(i,j)
                rows[j] = False
                columns[i] = False
    for row in rows :
        if row == True :
            changes[1] -= 1
        else:
            break
    rows.reverse()
    for row in rows :
        if row == True :
            changes[3] -= 1
        else:
            break
    for col in columns :
        if col == True :
            changes[0] -= 1
        else:
            break
    columns.reverse()
    for col in columns :
        if col == True :
            changes[2] -= 1
        else:
            break
    rows.reverse()
    columns.reverse()

    width = cursor.width + changes[0] + changes[2]
    height = cursor.height + changes[1] + changes[3]

    def pos_in_new_board(pos) :
        return (pos[0] + changes[0], pos[1] + changes[1])

    def is_in_new_board(pos) :
        (pos_x, pos_y) = pos_in_new_board(pos)
        return pos_x >= 0 and pos_x < width and pos_y >= 0 and pos_y < height

    new_walls = set()
    for w in cursor.walls :
        if is_in_new_board(w) :
            new_walls.add(pos_in_new_board(w))
    new_floors = set()
    for f in cursor.floors :
        if is_in_new_board(f) :
            new_floors.add(pos_in_new_board(f))
    new_boxes = []
    new_goals = []
    new_player_reach = set()
    for pos in cursor.boxes :
        if is_in_new_board(pos) :
            new_boxes.append(pos_in_new_board(pos))
    for pos in cursor.goals :
        if is_in_new_board(pos) :
            new_goals.append(pos_in_new_board(pos))
    for pos in cursor.player_reach :
        if is_in_new_board(pos) :
            new_player_reach.add(pos_in_new_board(pos))

    cursor.width = width
    cursor.height = height
    cursor.walls = new_walls
    cursor.floors = new_floors
    cursor.boxes = new_boxes
    cursor.goals = new_goals
    cursor.player_reach = new_player_reach

    print(changes)
    print(width, height)

    return cursor


def main():
    parser = argparse.ArgumentParser(description="Generate Sokoban levels")
    parser.add_argument("count", nargs='?', help="Number of levels to generate", type=int, default=2)
    parser.add_argument("-s", "--size", nargs=2, help="Min and max size of width or height of any level (default 9 and 11)", type=int, default=[9, 11])
#    parser.add_argument("maxsize", nargs='?', help="Max size of width or height of any level", type=int, default=11)
    parser.add_argument("-d", "--dir", help="Directory for storing the levels ('levels', must exist)", default='levels')
    
    args = parser.parse_args()
    count = args.count

    [minsize, maxsize] = args.size
     
    dir = args.dir

    if minsize<1 or minsize > maxsize:
        print('Sizes are not reasonable')
        return

    if not os.path.isdir(dir):
        print(f'Directory {dir} does not exist or is not a directory')
        return

    for _ in range(count):
        trying = True
        while trying:
            trying = not mcts(minsize,maxsize,dir)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Exception thrown:')
        print(e)

