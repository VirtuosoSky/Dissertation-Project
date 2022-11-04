'''---------- Importing librabries ----------'''

from ortools.sat.python import cp_model
import random

'''---------- Data ----------'''

n = 6
m = 5

num_s = n # Are these variables necessary - can't you just use n and m?
num_e = m
all_s = range(num_s)
all_e = range(num_e)

# I've added some random data for testing - could you do the same for experience?
PB = {}
for s in all_s:
    PB[s] = 1 # Everyone qualified
    if random.random() < .3:
        PB[s] = 0
    print(f"Sailor {s}: PB2 {PB[s]}")

'''---------- Creating model ----------'''

model = cp_model.CpModel()

'''---------- Creating variables ----------'''

# num_s = n
# num_e = m
# all_s = range(num_s)
# all_e = range(num_e)

# I don't think these need to be decision variables - should just be data as I've done above
# PB = {}
# for s in all_s:
#     PB[(s)] = model.NewBoolVar('Power_boat_s%i' % (s))

# Can you do the same for experience?
E = {}
for s in all_s:
    E[(s)] = model.NewBoolVar('Experienced_s%i' % (s))

# Creating decision variables
P = {}
for s in all_s:
    for e in all_e:
        P[(s, e)] = model.NewBoolVar('PRO_s%ie%i' % (s, e))

A = {}
for s in all_s:
    for e in all_e:
        A[(s, e)] = model.NewBoolVar('ARO_s%ie%i' % (s, e))

SB = {}
for s in all_s:
    for e in all_e:
        SB[(s, e)] = model.NewBoolVar('Safety_boat_s%ie%i' % (s, e))

'''---------- Constraints ----------'''

# Must be qualified
for s in all_s:
    SB_q = sum(SB[(s, e)] for e in all_e)
    model.Add(SB_q <= PB[s])
    # model.Add(SB_q <= 1)

# Must be experienced
for s in all_s:
    P_e = sum(P[(s, e)] for e in all_e)
    # model.Add(P_e <= E[(s)])
    model.Add(P_e <= 1)

# I think it's best to remove this for the moment
# Only one duty for each event
# for s in all_s:
#     for e in all_e:
#         model.Add((P[(s, e)] + A[(s, e)] + SB[(s, e)]) <= 1 )

# All duties filled
for e in all_e:
    model.AddExactlyOne(P[(s, e)] for s in all_s)
    model.AddExactlyOne(A[(s, e)] for s in all_s)
    model.AddExactlyOne(SB[(s, e)] for s in all_s)

'''---------- Find maximum and minimum number of duties allocated ----------'''

d = []

for s in all_s:
    di = model.NewIntVar(0, 3 * num_e, 'di')
    model.Add(di == sum((P[(s, e)] + A[(s, e)] + SB[(s, e)]) for e in all_e))
    d.append(di)
max_val = model.NewIntVar(0, 3 * num_e, 'max_val')
d_max = model.AddMaxEquality(max_val, d)
min_val = model.NewIntVar(0, 3 * num_e, 'min_val')
d_min = model.AddMinEquality(min_val, d)

'''---------- Objective: minimize (d_max - d_min) ----------'''

model.Minimize(max_val - min_val)

'''---------- Solver parameter update ----------'''

solver = cp_model.CpSolver()
solver.parameters.linearization_level = 0

'''---------- Enumerate all solutions ----------'''

solver.parameters.enumerate_all_solutions = True

'''---------- Register a callback ----------'''

class Test1SolutionPrinter(cp_model.CpSolverSolutionCallback):
    '''Print intermediate solutions'''

    def __init__(self, num_s, num_e, P, A, SB, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._num_s = num_s
        self._num_e = num_e
        self._P = P
        self._A = A
        self._SB = SB
        self._solution_count = 0
        self._solution_limit = limit
    
    def on_solution_callback(self):
        self._solution_count += 1
        print('Solution %i' % self._solution_count)
        for e in range(self._num_e):
            print('Event %i' % (e + 1))
            for s in range(self._num_s):
                is_playing = True
                if self.Value(self._P[(s, e)]):
                    is_playing = False
                    print('  Sailor %i works as PRO' % (s + 1))
                if self.Value(self._A[(s, e)]):
                    is_playing = False
                    print('  Sailor %i works as ARO' % (s + 1))
                if self.Value(self._SB[(s, e)]):
                    is_playing = False
                    print('  Sailor %i works on a safety boat' % (s + 1))
                if is_playing:
                    print('  Sailor %i is playing' % (s + 1))
        print('  There are %i most reasonable solutions' % self._solution_count)

        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count

'''---------- Display all the most reasonable solutions ----------'''

solution_limit = 999
solution_printer = Test1SolutionPrinter(num_s, num_e, P, A, SB, solution_limit)

'''---------- Launch a solver ----------'''

solver.Solve(model, solution_printer)
