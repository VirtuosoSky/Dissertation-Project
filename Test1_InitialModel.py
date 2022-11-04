'''---------- Importing libraries ----------'''

from ortools.sat.python import cp_model
import random

'''---------- Data ----------'''

n = 6
m = 5
all_s = range(n)
all_e = range(m)

PB = {}
for s in all_s:
    PB[s] = 1 # Everyone qualified
    if random.random() < .5:
        PB[s] = 0

E = {}
for s in all_s:
    E[s] = 1 # Everyone experienced
    if random.random() < .5:
        E[s] = 0
    print(f"Sailor {s+1}: PB {PB[s]} E {E[s]}")

'''---------- Creating model ----------'''

model = cp_model.CpModel()

'''---------- Creating decision variables ----------'''

P = {}
for s in all_s:
    for e in all_e:
        P[(s, e)] = model.NewBoolVar('PRO_s%ie%i' % (s, e))
        # print(f"Sailor {s+1} Events {e+1}: P {P[(s, e)]}")

A = {}
for s in all_s:
    for e in all_e:
        A[(s, e)] = model.NewBoolVar('ARO_s%ie%i' % (s, e))
        # print(f"Sailor {s+1} Events {e+1}: A {A[(s, e)]}")

SB = {}
for s in all_s:
    for e in all_e:
        SB[(s, e)] = model.NewBoolVar('Safety_boat_s%ie%i' % (s, e))
        # print(f"Sailor {s+1} Events {e+1}: SB {SB[(s, e)]}")

'''---------- Constraints ----------'''

# Must be qualified
for s in all_s:
    for e in all_e:
        model.Add(SB[(s, e)] <= PB[(s)])

# Must be experienced
for s in all_s:
    for e in all_e:
        model.Add(P[(s, e)] <= E[(s)])

# Only one duty for each event
for s in all_s:
    for e in all_e:
        model.Add((P[(s, e)] + A[(s, e)] + SB[(s, e)]) <= 1 )

# All duties filled
for e in all_e:
    model.AddExactlyOne(P[(s, e)] for s in all_s)
    model.AddExactlyOne(A[(s, e)] for s in all_s)
    model.AddExactlyOne(SB[(s, e)] for s in all_s)

'''---------- Find maximum and minimum number of duties allocated ----------'''

duty_s = {}
for s in all_s:
    duty_s[s] = model.NewIntVar(0, 3 * m, 'Number_of_duties_in_all_series_%s' % s)
    model.Add(duty_s[s] == sum((P[(s, e)] + A[(s, e)] + SB[(s, e)]) for e in all_e))

max_val = model.NewIntVar(0, 3 * m, 'max_val')
model.AddMaxEquality(max_val, [duty_s[s] for s in all_s])
min_val = model.NewIntVar(0, 3 * m, 'min_val')
model.AddMinEquality(min_val, [duty_s[s] for s in all_s])

'''---------- Objective: minimize (max_val - min_val) ----------'''

model.Minimize(max_val - min_val)

'''---------- Solver parameter update ----------'''

solver = cp_model.CpSolver()

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
            print('Event %i' % (e+1))
            for s in range(self._num_s):
                is_playing = True
                if self.Value(self._P[(s, e)]):
                    is_playing = False
                    print('  Sailor %i works as PRO' % (s+1))
                if self.Value(self._A[(s, e)]):
                    is_playing = False
                    print('  Sailor %i works as ARO' % (s+1))
                if self.Value(self._SB[(s, e)]):
                    is_playing = False
                    print('  Sailor %i works on a safety boat' % (s+1))
                if is_playing:
                    print('  Sailor %i is playing' % (s+1))

        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count

'''---------- Display the solutions ----------'''

solution_limit = 999
solution_printer = Test1SolutionPrinter( n, m, P, A, SB, solution_limit)

'''---------- Launch a solver ----------'''

solver.Solve(model, solution_printer)