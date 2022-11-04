'''---------- Importing libraries ----------'''

from ortools.sat.python import cp_model
import pandas as pd
from collections import Counter
import argparse

'''---------- Add command line arguments ----------'''

parser = argparse.ArgumentParser(description='A program to solve resource allocation problem.', add_help=False)
parser.add_argument('-h', '--help', action='help',
                    help='All the optional arguments should be separated by spaces.')
parser.add_argument('-add1', action='store_true',
                    help='add the constraint that sailors in double handed boats should be scheduled for duties at the same times.')
parser.add_argument('-add2', action='store_true',
                    help='add the constraint that sailors should only be allocated one duty in each series.')
parser.add_argument('-add3', action='store_true',
                    help='add the constraint that there has to be at least 3 races in between duties for each sailor.')
parser.add_argument('-add4', action='store_true',
                    help='add the constraint that sailors will not be allocated duties unless their preferred duties.')
args = parser.parse_args()

'''---------- Read csv file and input data----------'''

sailors = 'Sailors.csv'
race_calendar = 'Race calendar.csv'
unavailable_dates = 'Unavailable dates.csv'
crew = 'Crew.csv'

df_sailors = pd.read_csv(sailors)
all_s = []
for index, row in df_sailors.iterrows():
    all_s.append(row['Name'])

df_calendar = pd.read_csv(race_calendar)
series_name = []
for index, row in df_calendar.iterrows():
    series_name.append(row['Series'])
all_series = dict(Counter(series_name))
all_e = []
for index, row in df_calendar.iterrows():
    all_e.append(row['Date'])

df_unavailable_dates = pd.read_csv(unavailable_dates)

df_crew = pd.read_csv(crew)
# Error checking to make sure each sailor only occurs once in this file
try:
    checklist = []
    for index, row in df_crew.iterrows():
        checklist.append(row['HelmName'])
        if not pd.isnull(row['CrewName']):    
            checklist.append(row['CrewName'])
    Counter(checklist) == Counter(all_s)
except:
    print ('Each sailor occurs more than once in Crew.csv file')


PB = {}
for s in all_s:
    for index, row in df_sailors.iterrows():
        if row[0] == s:
            PB[s] = int(row[1])

E = {}
for s in all_s:
    for index, row in df_sailors.iterrows():
        if row[0] == s:
            E[s] = int(row[2])
    # print(f"Sailor {all_s.index(s)+1} {s} : PB {PB[s]} E {E[s]}")

# Preferred duties
P_PRO = {}
for s in all_s:
    for index, row in df_sailors.iterrows():
        if row[0] == s:
            P_PRO[s] = int(row[3])

P_ARO = {}
for s in all_s:
    for index, row in df_sailors.iterrows():
        if row[0] == s:
            P_ARO[s] = int(row[4])

P_SB = {}
for s in all_s:
    for index, row in df_sailors.iterrows():
        if row[0] == s:
            P_SB[s] = int(row[5])

'''---------- Creating model ----------'''

model = cp_model.CpModel()

'''---------- Creating decision variables ----------'''

P = {}
for s in all_s:
    for e in all_e:
        P[(s, e)] = model.NewBoolVar('PRO_%s_%s' % (s, e))

A = {}
for s in all_s:
    for e in all_e:
        A[(s, e)] = model.NewBoolVar('ARO_%s_%s' % (s, e))

SB_1 = {}
for s in all_s:
    for e in all_e:
        SB_1[(s, e)] = model.NewBoolVar('Safety_boat_1_%s_%s' % (s, e))

SB_2 = {}
for s in all_s:
    for e in all_e:
        SB_2[(s, e)] = model.NewBoolVar('Safety_boat_2_%s_%s' % (s, e))

# number of duties in each race
D = {}
for s in all_s:
    for e in all_e:
        D[(s, e)] = model.NewIntVar(0, 4, 'Number_of_duties_%s_%s' % (s, e))

'''---------- Constraints ----------'''
# D = P + A + SB_1 +SB_2
for s in all_s:
    for e in all_e:
        model.Add(D[(s, e)] == P[(s, e)] + A[(s, e)] + SB_1[(s, e)] + SB_2[(s, e)])

# Must be qualified
for s in all_s:
    for e in all_e:
        model.Add(SB_1[(s, e)] <= PB[(s)])

# Must be experienced
for s in all_s:
    for e in all_e:
        model.Add(P[(s, e)] <= E[(s)])

# No one scheduled when they are unavailable
for s in all_s:
    for e in all_e:
        if ((df_unavailable_dates['Name'] == s) & (df_unavailable_dates['Unavailable'] == e)).any():
            model.Add(D[(s, e)] == 0)

# Only one duty for each event
for s in all_s:
    for e in all_e:
            model.Add(D[(s, e)] <= 1 )

# All duties filled
for e in all_e:
    model.AddExactlyOne(P[(s, e)] for s in all_s)
    model.AddExactlyOne(A[(s, e)] for s in all_s)
    model.AddExactlyOne(SB_1[(s, e)] for s in all_s)
    model.AddExactlyOne(SB_2[(s, e)] for s in all_s)

# Sailors in double handed boats should be scheduled for duties at the same times
if args.add1:
    for e in all_e:
        for s in all_s:
            for index, row in df_crew.iterrows():
                if row['HelmName'] == s:
                    if not pd.isnull(row['CrewName']):
                        model.Add(D[(s, e)] == D[(row['CrewName'], e)])
                else:
                    if row['CrewName'] == s:
                        model.Add(D[(s, e)] == D[(row['HelmName'], e)])

# Sailors should only be allocated one duty in each series
if args.add2:
    for s in all_s:
        for se in all_series:
            series = []
            for index, row in df_calendar.iterrows():
                if row['Series'] == se:
                    series.append(row['Date'])
            model.Add(sum(D[(s, e)] for e in series) <= 1)

# There has to be at least 3 races in between duties for each sailor
if args.add3:
    for s in all_s:
        all_e_1 = all_e[:-3 or None]
        for e in all_e_1:
            i = all_e.index(e)
            model.Add(D[(s, e)] + D[(s, all_e[i+1])] + D[(s, all_e[i+2])] + D[(s, all_e[i+3])] <= 1)

# Preferred duties
if args.add4:
    for s in all_s:
        for e in all_e:
            if P_PRO[s] == 0:
                model.Add(P[(s, e)] == 0)
            if P_ARO[s] == 0:
                model.Add(A[(s, e)] == 0)
            if P_SB[s] == 0:
                model.Add(SB_1[(s, e)] + SB_2[(s, e)] == 0)

'''---------- Find maximum and minimum number of duties allocated ----------'''

duty_s = {}
for s in all_s:
    duty_s[s] = model.NewIntVar(0, len(all_e), 'Number_of_duties_in_all_series_%s' % s)
    model.Add(duty_s[s] == sum(D[(s, e)] for e in all_e))

max_val = model.NewIntVar(0, len(all_e), 'max_val')
model.AddMaxEquality(max_val, [duty_s[s] for s in all_s])
min_val = model.NewIntVar(0, len(all_e), 'min_val')
model.AddMinEquality(min_val, [duty_s[s] for s in all_s])



'''---------- Objective: minimize (d_max - d_min) ----------'''

model.Minimize(max_val - min_val)

'''---------- Solver parameter update ----------'''

solver = cp_model.CpSolver()


'''---------- Register a callback ----------'''

class Test1SolutionPrinter(cp_model.CpSolverSolutionCallback):
    '''Print intermediate solutions'''

    def __init__(self, all_s, all_e, P, A, SB_1, SB_2, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._all_s = all_s
        self._all_e = all_e
        self._P = P
        self._A = A
        self._SB_1 = SB_1
        self._SB_2 = SB_2
        self._solution_count = 0
        self._solution_limit = limit
    
    def on_solution_callback(self):
        self._solution_count += 1
        print('')
        print('Solution %i' % self._solution_count)
        for e in self._all_e:
            for s in self._all_s:
                is_playing = True
                if self.Value(self._P[(s, e)]):
                    is_playing = False
                    df_calendar.loc[df_calendar.Date == e, 'Principal Race Officer'] = s
                if self.Value(self._A[(s, e)]):
                    is_playing = False
                    df_calendar.loc[df_calendar.Date == e, 'Assistant Race Officer'] = s
                if self.Value(self._SB_1[(s, e)]):
                    is_playing = False
                    df_calendar.loc[df_calendar.Date == e, 'Safety Boat 1'] = s
                if self.Value(self._SB_2[(s, e)]):
                    is_playing = False
                    df_calendar.loc[df_calendar.Date == e, 'Safety Boat 2'] = s

        print('Objective value: %i' % self.ObjectiveValue())
        print('Max duties: %i' % self.Value(max_val))
        print('Min duties: %i' % self.Value(min_val))
        
        aver = sum(self.Value(duty_s[s]) for s in all_s) / len(all_s)
        print('Weighted average duties: %f' % aver)

        duty_f = {}
        for s in all_s:
            duty_f[s] = self.Value(duty_s[s])
        for s in sorted(duty_f, key=duty_f.get, reverse=True):
            print('Sailor: %s Duties: %i' % (s, duty_f[s]))

        print('There are %i solutions.' % self._solution_count)
        
        df_calendar.to_csv('Race calendar.csv', index=False)

        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count

'''---------- Display all the most reasonable solutions ----------'''

solution_limit = 999
solution_printer = Test1SolutionPrinter(all_s, all_e, P, A, SB_1, SB_2, solution_limit)

'''---------- Launch a solver ----------'''

status = solver.Solve(model, solution_printer)
if status == cp_model.OPTIMAL:
    print('')
    print('There is an optimal solution.')
    print('Optimal objective value: %i' % solver.ObjectiveValue())
    print('Max duties: %i' % solver.Value(max_val))
    print('Min duties: %i' % solver.Value(min_val))
    
    aver = sum(solver.Value(duty_s[s]) for s in all_s) / len(all_s)
    print('Weighted average duties: %f' % aver)

    duty_o = {}
    for s in all_s:
        duty_o[s] = solver.Value(duty_s[s])
    for s in sorted(duty_o, key=duty_o.get, reverse=True):
        print('Sailor: %s Duties: %i' % (s, duty_o[s]))
elif status == cp_model.FEASIBLE:
    print('This problem has feasible solutions')
elif status == cp_model.INFEASIBLE:
    print('This problem has no solutions')
else:
    print('Error')