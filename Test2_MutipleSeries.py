'''---------- Importing librabries ----------'''

from ortools.sat.python import cp_model
import random

'''---------- Data ----------'''

n = 15
m = 5
series = 5

all_s = range(n)
all_e = range(m)
all_series = range(series)

PB = {}
for s in all_s:
    PB[s] = 1
    if random.random() < .3:
        PB[s] = 0

E = {}
for s in all_s:
    E[s] = 1
    if random.random() < .3:
        E[s] = 0
    print(f"Sailor {s+1}: PB {PB[s]} E {E[s]}")

'''---------- Creating model ----------'''

model = cp_model.CpModel()

'''---------- Creating decision variables ----------'''

P = {}
for s in all_s:
    for se in all_series:
        for e in all_e:
            P[(s, se, e)] = model.NewBoolVar('PRO_s%ise%ie%i' % (s, se, e))

A = {}
for s in all_s:
    for se in all_series:
        for e in all_e:
            A[(s, se, e)] = model.NewBoolVar('ARO_s%ise%ie%i' % (s, se, e))

SB = {}
for s in all_s:
    for se in all_series:
        for e in all_e:
            SB[(s, se, e)] = model.NewBoolVar('Safety_boat_s%ise%ie%i' % (s, se, e))

'''---------- Constraints ----------'''

# Must be qualified
for s in all_s:
    for se in all_series:
        for e in all_e:
            model.Add(SB[(s, se, e)] <= PB[(s)])

# Must be experienced
for s in all_s:
    for se in all_series:
        for e in all_e:
            model.Add(P[(s, se, e)] <= E[(s)])

# Only one duty for each event
for se in all_series:    
    for s in all_s:
        for e in all_e:
            model.Add((P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)]) <= 1 )

# All duties filled
for se in all_series:
    for e in all_e:
        model.AddExactlyOne(P[(s, se, e)] for s in all_s)
        model.AddExactlyOne(A[(s, se, e)] for s in all_s)
        model.AddExactlyOne(SB[(s, se, e)] for s in all_s)

# Sailors should only be allocated one duty in each series
for s in all_s:
    for se in all_series:
        model.Add(sum((P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)]) for e in all_e) <= 1)

'''---------- Find maximum and minimum number of duties allocated ----------'''

d = []

for se in all_series:
    for s in all_s:
        di = model.NewIntVar(0, 3 * m, 'di')
        model.Add(di == sum((P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)]) for e in all_e))
        d.append(di)

max_val = model.NewIntVar(0, 3 * m, 'max_val')
model.AddMaxEquality(max_val, d)
min_val = model.NewIntVar(0, 3 * m, 'min_val')
model.AddMinEquality(min_val, d)

'''---------- Objective: minimize (d_max - d_min) ----------'''

model.Minimize(max_val - min_val)

'''---------- Solver parameter update ----------'''

solver = cp_model.CpSolver()
# solver.parameters.linearization_level = 0

'''---------- Enumerate all solutions ----------'''

solver.parameters.enumerate_all_solutions = True

'''---------- Register a callback ----------'''

class Test1SolutionPrinter(cp_model.CpSolverSolutionCallback):
    '''Print intermediate solutions'''

    def __init__(self, num_s, num_e, num_se, P, A, SB, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._num_s = num_s
        self._num_e = num_e
        self._num_se = num_se
        self._P = P
        self._A = A
        self._SB = SB
        self._solution_count = 0
        self._solution_limit = limit
    
    def on_solution_callback(self):
        self._solution_count += 1
        print('Solution %i' % self._solution_count)
        for se in range(self._num_se):
            print('Series %i' % (se+1))
            for e in range(self._num_e):
                print('  Event %i' % (e+1))
                for s in range(self._num_s):
                    is_playing = True
                    if self.Value(self._P[(s, se, e)]):
                        is_playing = False
                        print('    Sailor %i works as PRO' % (s+1))
                    if self.Value(self._A[(s, se, e)]):
                        is_playing = False
                        print('    Sailor %i works as ARO' % (s+1))
                    if self.Value(self._SB[(s, se, e)]):
                        is_playing = False
                        print('    Sailor %i works on a safety boat' % (s+1))
                    if is_playing:
                        print('    Sailor %i is playing' % (s+1))

        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count

'''---------- Display all the most reasonable solutions ----------'''

solution_limit = 999
solution_printer = Test1SolutionPrinter( n, m, series, P, A, SB, solution_limit)

'''---------- Launch a solver ----------'''

status = solver.Solve(model, solution_printer)
if status == cp_model.OPTIMAL:
    print('Optimal cost: %i' % solver.ObjectiveValue())
    print('Max duties: %i' % solver.Value(max_val))
    print('Min duties: %i' % solver.Value(min_val))