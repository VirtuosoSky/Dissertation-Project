'''---------- Importing librabries ----------'''

from ortools.sat.python import cp_model
import random
import csv
from collections import Counter

'''---------- Read csv file and input data----------'''

with open('Sailors.csv') as file:
    csv_reader = csv.reader(file, delimiter=',')
    list_sailors = list(csv_reader)
    list_sailors.pop(0)
    for i in list_sailors[:]:
        if i[0] == '':
            list_sailors.remove(i)

with open('Race calendar.csv') as file:
    csv_reader = csv.reader(file, delimiter=',')
    list_calendar = list(csv_reader)
    list_calendar.pop(0)

    series_name = []
    for i in list_calendar:
        series_name.append(i[1])
    series = dict(Counter(series_name))

with open('Unavailable dates.csv') as file:
    csv_reader = csv.reader(file, delimiter=',')
    list_dates = list(csv_reader)
    list_dates.pop(0)

all_s = []
for i in list_sailors:
    all_s.append(i[0])

PB = {}
for s in all_s:
    for i in list_sailors:
        if i[0] == s:
            PB[s] = int(i[1])

E = {}
for s in all_s:
    for i in list_sailors:
        if i[0] == s:
            E[s] = int(i[2])
    print(f"Sailor {all_s.index(s)+1} {s} : PB {PB[s]} E {E[s]}")

'''---------- Creating model ----------'''

model = cp_model.CpModel()

'''---------- Creating decision variables ----------'''

P = {}
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        for e in all_e:
            P[(s, se, e)] = model.NewBoolVar('PRO_%s_%s_%s' % (s, se, e))

A = {}
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        for e in all_e:
            A[(s, se, e)] = model.NewBoolVar('ARO_%s_%s_%s' % (s, se, e))

SB = {}
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        for e in all_e:
            SB[(s, se, e)] = model.NewBoolVar('Safety_boat_%s_%s_%s' % (s, se, e))

'''---------- Constraints ----------'''

# Must be qualified
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        for e in all_e:
            model.Add(SB[(s, se, e)] <= PB[(s)])

# Must be experienced
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        for e in all_e:
            model.Add(P[(s, se, e)] <= E[(s)])

# No one scheduled when they are unavailable
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        for e in all_e:
            if [s, e] in list_dates:
                model.Add(P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)] == 0)

# Only one duty for each event
for se in series:
    all_e = []
    for i in list_calendar:
        if i[1] == se:
            all_e.append(i[0])
    for e in all_e:
        for s in all_s:
            model.Add((P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)]) <= 1 )

# All duties filled
for se in series:
    all_e = []
    for i in list_calendar:
        if i[1] == se:
            all_e.append(i[0])
    for e in all_e:
        model.AddExactlyOne(P[(s, se, e)] for s in all_s)
        model.AddExactlyOne(A[(s, se, e)] for s in all_s)
        model.AddExactlyOne(SB[(s, se, e)] for s in all_s)

# Sailors should only be allocated one duty in each series
for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        model.Add(sum((P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)]) for e in all_e) <= 1)

'''---------- Find maximum and minimum number of duties allocated ----------'''

duties = []

for s in all_s:
    for se in series:
        all_e = []
        for i in list_calendar:
            if i[1] == se:
                all_e.append(i[0])
        duty = model.NewIntVar(0, 3 * len(list_calendar), 'duty')
        duty = sum((P[(s, se, e)] + A[(s, se, e)] + SB[(s, se, e)]) for e in all_e)
        duties.append(duty)

max_val = model.NewIntVar(0, 3 * len(list_calendar), 'max_val')
model.AddMaxEquality(max_val, duties)
min_val = model.NewIntVar(0, 3 * len(list_calendar), 'min_val')
model.AddMinEquality(min_val, duties)

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

    def __init__(self, all_s, series, P, A, SB, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._all_s = all_s
        self._series = series
        self._P = P
        self._A = A
        self._SB = SB
        self._solution_count = 0
        self._solution_limit = limit
    
    def on_solution_callback(self):
        self._solution_count += 1
        print('Solution %i' % self._solution_count)
        for se in self._series:
            print('Series %s' % (se))
            all_e = []
            for i in list_calendar:
                if i[1] == se:
                    all_e.append(i[0])
            for e in all_e:
                print('  Event %s' % (e))
                for s in self._all_s:
                    if [s, e] in list_dates:
                        is_playing = False
                        print('    Sailor %s is unavailable today' % (s))
                    else:
                        is_playing = True
                        if self.Value(self._P[(s, se, e)]):
                            is_playing = False
                            print('    Sailor %s works as PRO' % (s))
                            
                            for i in list_calendar:
                                if i[0] == e:
                                    i[3] = s
                        if self.Value(self._A[(s, se, e)]):
                            is_playing = False
                            print('    Sailor %s works as ARO' % (s))
                            
                            for i in list_calendar:
                                if i[0] == e:
                                    i[4] = s
                        if self.Value(self._SB[(s, se, e)]):
                            is_playing = False
                            print('    Sailor %s works on a safety boat' % (s))
                            
                            for i in list_calendar:
                                if i[0] == e:
                                    i[5] = s
                        if is_playing:
                            print('    Sailor %s is playing' % (s))
        print('There are %i solutions.' % self._solution_count)
        
        with open('Race calendar.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Date','Series','Dinghy Start Time','Principal Race Officer','Assistant Race Officer','Safety Boat ','Safety Boat'])
            writer.writerows(list_calendar)

        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count

'''---------- Display all the most reasonable solutions ----------'''

solution_limit = 999
solution_printer = Test1SolutionPrinter(all_s, series, P, A, SB, solution_limit)

'''---------- Launch a solver ----------'''

status = solver.Solve(model, solution_printer)
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('Optimal objective value: %i' % solver.ObjectiveValue())
    print('Max duties: %i' % solver.Value(max_val))
    print('Min duties: %i' % solver.Value(min_val))
elif status == cp_model.INFEASIBLE:
    print('INFEASIBLE SOLUTION')
else:
    print('No solutions')
