'''---------- Importing librabries ----------'''

from ortools.sat.python import cp_model
import pandas as pd
from collections import Counter

'''---------- Read csv file and input data----------'''

sailors = 'Sailors.csv'
race_calendar = 'Race calendar.csv'
unavailable_dates = 'Unavailable dates.csv'
crew = 'Crew.csv'

df_sailors = pd.read_csv(sailors)
df_sailors.dropna(inplace=True)
df = df_sailors.reset_index(drop=True)
all_s = []
for index, row in df_sailors.iterrows():
    all_s.append(row['Name'])

df_calendar = pd.read_csv(race_calendar)
series_name = []
for index, row in df_calendar.iterrows():
    series_name.append(row['Series'])
series = dict(Counter(series_name))

df_dates = pd.read_csv(unavailable_dates)

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
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            P[(s, se, e)] = model.NewBoolVar('PRO_%s_%s_%s' % (s, se, e))

A = {}
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            A[(s, se, e)] = model.NewBoolVar('ARO_%s_%s_%s' % (s, se, e))

SB_1 = {}
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            SB_1[(s, se, e)] = model.NewBoolVar('Safety_boat_1_%s_%s_%s' % (s, se, e))

SB_2 = {}
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            SB_2[(s, se, e)] = model.NewBoolVar('Safety_boat_2_%s_%s_%s' % (s, se, e))

# number of duties in each race
D = {}
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            D[(s, se, e)] = model.NewIntVar(0, 4, 'Number_of_duties_%s_%s_%s' % (s, se, e))

'''---------- Constraints ----------'''

# Must be qualified
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            model.Add(SB_1[(s, se, e)] <= PB[(s)])

# Must be experienced
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            model.Add(P[(s, se, e)] <= E[(s)])

# No one scheduled when they are unavailable
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            if ((df_dates['Name'] == s) & (df_dates['Unavailable'] == e)).any():
                model.Add(D[(s, se, e)] == 0)

# Only one duty for each event
for se in series:
    all_e = []
    for index, row in df_calendar.iterrows():
        if row[1] == se:
            all_e.append(row[0])
    for e in all_e:
        for s in all_s:
            # model.Add((P[(s, se, e)] + A[(s, se, e)] + SB_1[(s, se, e)] + SB_2[(s, se, e)]) <= 1 )
            model.Add(D[(s, se, e)] <= 1 )

# All duties filled
for se in series:
    all_e = []
    for index, row in df_calendar.iterrows():
        if row[1] == se:
            all_e.append(row[0])
    for e in all_e:
        model.AddExactlyOne(P[(s, se, e)] for s in all_s)
        model.AddExactlyOne(A[(s, se, e)] for s in all_s)
        model.AddExactlyOne(SB_1[(s, se, e)] for s in all_s)
        model.AddExactlyOne(SB_2[(s, se, e)] for s in all_s)

# Sailors in double handed boats should be scheduled for duties at the same times
for se in series:
    all_e = []
    for index, row in df_calendar.iterrows():
        if row[1] == se:
            all_e.append(row[0])
    for e in all_e:
        for s in all_s:
            for index, row in df_crew.iterrows():
                if row['HelmName'] == s:
                    if not pd.isnull(row['CrewName']):
                        model.Add(D[(s, se, e)] == D[(row['CrewName'], se, e)])
                else:
                    if row['CrewName'] == s:
                        model.Add(D[(s, se, e)] == D[(row['HelmName'], se, e)])

# D = P + A + SB_1 +SB_2
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            model.Add(D[(s, se, e)] == P[(s, se, e)] + A[(s, se, e)] + SB_1[(s, se, e)] + SB_2[(s, se, e)])

# # Sailors should only be allocated one duty in each series
# for s in all_s:
#     for se in series:
#         all_e = []
#         for index, row in df_calendar.iterrows():
#             if row[1] == se:
#                 all_e.append(row[0])
#         model.Add(sum((D[(s, se, e)] for e in all_e) <= 1)

# # There has to be at least 3 races in between duties for each sailor
# for s in all_s:
#     for se in series:
#         all_e = []
#         for index, row in df_calendar.iterrows():
#             if row[1] == se:
#                 all_e.append(row[0])
#         for e in all_e:
#             i = all_e.index(e)
#             bool_test = model.NewBoolVar('')
#             model.Add(D[(s, se, e)] == 1).OnlyEnforceIf(bool_test)
#             model.Add(D[(s, se, e)] == 0).OnlyEnforceIf(bool_test.Not())

#             se1 = df_calendar.loc[df_calendar.Date == all_e[i+1], 'Series']
#             model.Add(D[(s, se1, all_e[i+1])] == 0).OnlyEnforceIf(bool_test)
#             # model.Add(D[(s, se1, all_e[i+2])] == 0).OnlyEnforceIf(bool_test)
#             # model.Add(D[(s, se1, all_e[i+3])] == 0).OnlyEnforceIf(bool_test)
#             # model.Add(D[(s, se1, all_e[i+1])] >= 0).OnlyEnforceIf(bool_test.Not())
#             # model.Add(D[(s, se1, all_e[i+2])] >= 0).OnlyEnforceIf(bool_test.Not())
#             # model.Add(D[(s, se1, all_e[i+3])] >= 0).OnlyEnforceIf(bool_test.Not())

# Preferred duties
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        for e in all_e:
            if P_PRO[s] == 0:
                model.Add(P[(s, se, e)] == 0)
            if P_ARO[s] == 0:
                model.Add(A[(s, se, e)] == 0)
            if P_SB[s] == 0:
                model.Add(SB_1[(s, se, e)] + SB_2[(s, se, e)] == 0)

'''---------- Find maximum and minimum number of duties allocated ----------'''

duty_se = {}
duty_s = {}
for s in all_s:
    for se in series:
        all_e = []
        for index, row in df_calendar.iterrows():
            if row[1] == se:
                all_e.append(row[0])
        duty_se[(s, se)] = model.NewIntVar(0, len(all_e), 'Number_of_duties_in_one_series_%s_%s' % (s, se))
        model.Add(duty_se[(s, se)] == sum(D[(s, se, e)] for e in all_e))
    duty_s[s] = model.NewIntVar(0, len(df_calendar), 'Number_of_duties_in_all_series_%s' % s)
    model.Add(duty_s[s] == sum(duty_se[(s, se)] for se in series))

max_val = model.NewIntVar(0, len(df_calendar), 'max_val')
model.AddMaxEquality(max_val, [duty_s[s] for s in all_s])
min_val = model.NewIntVar(0, len(df_calendar), 'min_val')
model.AddMinEquality(min_val, [duty_s[s] for s in all_s])



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

    def __init__(self, all_s, series, P, A, SB_1, SB_2, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._all_s = all_s
        self._series = series
        self._P = P
        self._A = A
        self._SB_1 = SB_1
        self._SB_2 = SB_2
        self._solution_count = 0
        self._solution_limit = limit
    
    def on_solution_callback(self):
        self._solution_count += 1
        print('Solution %i' % self._solution_count)
        for se in self._series:
            all_e = []
            for index, row in df_calendar.iterrows():
                if row[1] == se:
                    all_e.append(row[0])
            for e in all_e:
                for s in self._all_s:
                    is_playing = True
                    if ((df_dates['Name'] == s) & (df_dates['Unavailable'] == e)).any():
                        is_playing = False
                    else:
                        is_playing = True
                        if self.Value(self._P[(s, se, e)]):
                            is_playing = False
                            df_calendar.loc[df_calendar.Date == e, 'Principal Race Officer'] = s
                        if self.Value(self._A[(s, se, e)]):
                            is_playing = False
                            df_calendar.loc[df_calendar.Date == e, 'Assistant Race Officer'] = s
                        if self.Value(self._SB_1[(s, se, e)]):
                            is_playing = False
                            df_calendar.loc[df_calendar.Date == e, 'Safety Boat 1'] = s
                        if self.Value(self._SB_2[(s, se, e)]):
                            is_playing = False
                            df_calendar.loc[df_calendar.Date == e, 'Safety Boat 2'] = s

        print('Objective value: %i' % self.ObjectiveValue())
        print('Max duties: %i' % self.Value(max_val))
        print('Min duties: %i' % self.Value(min_val))
        
        aver = sum(self.Value(duty_s[s]) for s in all_s) // len(all_s)
        print('Weighted average duties: %i' % aver)

        for s in all_s:
            print('Salior: %s Duty: %i' % (s, self.Value(duty_s[s])))

        print('There are %i solutions.' % self._solution_count)
        
        # print(df_calendar)
        df_calendar.to_csv('Race calendar.csv', index=False)

        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count

'''---------- Display all the most reasonable solutions ----------'''

solution_limit = 999
solution_printer = Test1SolutionPrinter(all_s, series, P, A, SB_1, SB_2, solution_limit)

'''---------- Launch a solver ----------'''

status = solver.Solve(model, solution_printer)
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    print('This is the optimal solution.')
    print('Optimal objective value: %i' % solver.ObjectiveValue())
    print('Max duties: %i' % solver.Value(max_val))
    print('Min duties: %i' % solver.Value(min_val))
    
    aver = sum(solver.Value(duty_s[s]) for s in all_s) // len(all_s)
    print('Weighted average duties: %i' % aver)

    sorted_dict = sorted(duty_s.items(), key=lambda x: x[1], reverse=True)
    for key, value in sorted_dict:
        print('Sailor: %s Duties: %i' % (key, value))

    for s in all_s:
        print('Salior: %s' % s)
        for se in series:
            print('  Series: %s Duty: %i' % (se, solver.Value(duty_se[(s, se)])))
            all_e = []
            for index, row in df_calendar.iterrows():
                if row[1] == se:
                    all_e.append(row[0])
            for e in all_e:
                print('    Date: %s Duty: %i' % (e, solver.Value(D[(s, se, e)])))
        print('Salior: %s Duty: %i' % (s, solver.Value(duty_s[s])))
elif status == cp_model.INFEASIBLE:
    print('INFEASIBLE SOLUTION')
else:
    print('No solutions')