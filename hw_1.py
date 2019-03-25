from copy import deepcopy

class Puzzle(object):

    def __init__(self, matrix, goal=None, astar=False):
        self.o_pos_to_num = {}  # original alignment position to number
        self.o_num_to_pos = {}  # original alignment number to position
        
        self.pos_to_num = {}    # changable alignments, position to number
        self.num_to_pos = {}    # changable alignment, number to position
        self.parse_string(matrix) 

        self.goal = goal        # goal puzzle
        self.manhattan = lambda x, y: abs(x[0] - y[0]) + abs(x[1] - y[1]) # lambda function for calculating manhattan distance

        self.astar = astar      # whether we are going to use a* or ida* algorithm
        if self.astar:
            self.previous_branches = [] # initialize previous branches as a list
            self.out = "outputA.txt"    # output file if a* used
        else:
            self.out = "outputIDA.txt"  # output file if ida* uesd

        self.output = ""                # the string we are going to write in file

        if goal:                        # if this puzzle is the goal puzzle
            self.score_scheme = []      # a list contains tuples, (score, tuple pointer)
            self.branches = {
                "g_score" : 0,          # depth score
                "h_score" : self.calc_manhattan(self.goal), # heuristic score
                "branches": [],         # a list stores branches
                "parent"  : None        # a pointer stores parent node
            }

            self.current_branch = self.branches # set initial state as current branch

    def serialize(self):
        """serialize 8-puzzle as a list"""
        out_list = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        for num, (i, j) in self.num_to_pos.items():
            out_list[i][j] = num

        return out_list

    def parse_string(self, matrix):
        """parses list into dictionary"""
        for idx, row in enumerate(matrix):
            for idy, item in enumerate(row):
                self.o_pos_to_num[(idx, idy)] = item
                self.pos_to_num[(idx, idy)] = item
                self.o_num_to_pos[item] = (idx, idy)
                self.num_to_pos[item] = (idx, idy)

    def __originate__(self):
        """returns to start state"""
        self.pos_to_num = deepcopy(self.o_pos_to_num)
        self.num_to_pos = deepcopy(self.o_num_to_pos)

    def __getpos__(self, num):
        """get position of given number"""
        return self.num_to_pos[num]

    def __getnum__(self, i, j):
        """get number of given position"""
        return self.pos_to_num[(i, j)]

    def __getitem__(self, ids):
        """check whether it is a position or number"""
        if isinstance(ids, tuple):
            return self.__getnum__(ids[0], ids[1])

        elif isinstance(ids, int):
            return self.__getpos__(ids)

        else:
            raise RuntimeError("No such indexing exist")

    def __eq__(self, p_object):
        """check whether two puzzles are same"""
        if any([self[i] != p_object[i] for i in range(9)]):
            return False
        return True

    def __str__(self):
        """stringfy the puzzles current state"""
        outstr = ""
        for i in range(3):
            for j in range(3):
                outstr += str(self.pos_to_num[(i, j)]) + " "
            outstr = outstr[:-1]
            outstr += "\n"
        outstr += "\n"
        return outstr

    def calc_manhattan(self, p_object):
        """for calculating the manhattan distance"""
        total = sum([self.manhattan(self[num], p_object[num]) for num in sorted(self.num_to_pos)[1:]])
        return total

    def get_near_ones(self):
        """obtain the cells for change"""
        near_ones = []
        z_i, z_j = self[0]
        for i, j in [(-1, 0), (0, -1), (1, 0), (0, 1)]:
            try:
                near_ones.append(self[(z_i+i, z_j+j)])
            except KeyError:
                pass

        return near_ones

    def change(self, num):
        """function which change cells"""
        if self.manhattan(self[0], self[num]) != 1:
            raise RuntimeError(
                "Numbers {} {} in positions {} {} can't change".format(0, num, self[0], self[num]))

        z_i, z_j = self[0]
        n_i, n_j = self[num]

        self.pos_to_num[(z_i, z_j)] = num
        self.pos_to_num[(n_i, n_j)] = 0

        self.num_to_pos[0]      = (n_i, n_j)
        self.num_to_pos[num]    = (z_i, z_j)

    def branchize(self):
        """function which expand current node"""
        near_ones = self.get_near_ones()

        if self.current_branch["g_score"] == 31:
            return

        for item in near_ones:

            if self.current_branch.get("move") and self.current_branch["move"] == item:
                continue

            self.change(item)

            if self.astar:
                serialized = self.serialize()
                if serialized in self.previous_branches:
                    self.change(item)
                    continue
                else:
                    self.previous_branches.append(serialized)

            a_branch = {
                "status"    : True,
                "move"      : item,
                "g_score"   : self.current_branch["g_score"] + 1,
                "h_score"   : self.calc_manhattan(self.goal),
                "branches"  : [],
                "parent"    : self.current_branch
            }
            a_branch["f_score"] = a_branch["g_score"] + a_branch["h_score"]

            self.current_branch["branches"].append(a_branch)
            self.score_scheme.append((a_branch["f_score"], a_branch))
            self.change(item)

        self.score_scheme.sort(key=lambda x: x[0])

    def next_move(self):
        """decides which way to go"""
        self.branchize()
        try:
            _, new_branch = self.score_scheme.pop(0)
        except IndexError:
            return False

        move_list = [new_branch["move"]]
        parent = new_branch["parent"]

        while True:
            try:
                move_list.append(parent["move"])   
                parent = parent["parent"]

            except KeyError:
                break

        self.__originate__()
        for i in move_list[::-1]:
            self.change(i)

        self.current_branch = new_branch
        self.output += str(self)
        return True

    def solve(self):

        while self != self.goal:
            solveable = self.next_move()
            if not solveable:
                self.output = "fail\n\n"

        with open(self.out, "w") as file_:
            file_.write(self.output[:-2])

        print(self.current_branch["g_score"])

def parse_file(filename):
    with open(filename) as file_:
        lines = file_.readlines()
    list_a = [[int(item) for item in row.split()] for row in lines[:3]]
    list_b = [[int(item) for item in row.split()] for row in lines[4:7]]
    return list_a, list_b

def main():
    init, goal  = parse_file("input.txt")
    goal_puzzle = Puzzle(goal)
    init_a      = Puzzle(init, goal_puzzle, True)
    init_ida    = Puzzle(init, goal_puzzle, False)

    init_a.solve()
    init_ida.solve()

if __name__ == "__main__":
    main()
    # print(puz_a[(1,2)])
    # print(puz_a == puz_b)

    # print(puz_a.calc_manhattan(puz_b))

    # print("goal:\n{}".format( puz_b))
    # print(puz_a.serialize())
    # near = puz_a.get_near_ones()
    # puz_a.change(near[0])
    # print(puz_a)

    # puz_a.branchize()
    # puz_a.next_move()

    # puz_a.solve()
    # puz_ida.solve()
