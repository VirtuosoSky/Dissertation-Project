'''---------- Importing libraries ----------'''

from ortools.sat.python import cp_model
import random
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

'''---------- Input data----------'''

n = 26
m = 60
all_s = range(n)
all_e = range(m)

test_percentage = 0.18
PB = {}
for s in all_s:
    PB[s] = 1 # Everyone not qualified

E = {}
for s in all_s:
    E[s] = 0 # Everyone not experienced
    if s < n * test_percentage:
        E[s] = 1

# Preferred duties
P_PRO = {}
for s in all_s:
    P_PRO[s] = 1 # Everyone prefer to do PRO
    # if random.random() < .5:
    #     P_PRO[s] = 0

P_ARO = {}
for s in all_s:
    P_ARO[s] = 1 # Everyone prefer to do ARO
    # if random.random() < .5:
    #     P_ARO[s] = 0


P_SB = {}
for s in all_s:
    P_SB[s] = 1 # Everyone prefer to do safety boat
    # if random.random() < .5:
    #     P_SB[s] = 0
    print(f"Sailor {s}: PB {PB[s]} E {E[s]} P_PRO {P_PRO[s]} P_ARO {P_ARO[s]} P_SB {P_SB[s]}")

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

# # No one scheduled when they are unavailable
# for s in all_s:
#     for e in all_e:
#         if ((df_unavailable_dates['Name'] == s) & (df_unavailable_dates['Unavailable'] == e)).any():
#             model.Add(D[(s, e)] == 0)

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

# # Sailors in double handed boats should be scheduled for duties at the same times
# if args.add1:
#     for e in all_e:
#         for s in all_s:
#             for index, row in df_crew.iterrows():
#                 if row['HelmName'] == s:
#                     if not pd.isnull(row['CrewName']):
#                         model.Add(D[(s, e)] == D[(row['CrewName'], e)])
#                 else:
#                     if row['CrewName'] == s:
#                         model.Add(D[(s, e)] == D[(row['HelmName'], e)])

# # Sailors should only be allocated one duty in each series
# if args.add2:
#     for s in all_s:
#         for se in all_series:
#             series = []
#             for index, row in df_calendar.iterrows():
#                 if row['Series'] == se:
#                     series.append(row['Date'])
#             model.Add(sum(D[(s, e)] for e in series) <= 1)

# There has to be at least 3 races in between duties for each sailor
if args.add3:
    for s in all_s:
        all_e = list(all_e)
        all_e_1 = all_e[:-3 or None]
        for e in all_e_1:
            i = all_e.index(e)
            model.Add(D[(s, e)] + D[(s, all_e[i+1])] + D[(s, all_e[i+2])] + D[(s, all_e[i+3])] <= 1)

# Preferred duties
num_not_preferred = model.NewIntVar(0, 4 * len(all_e), 'Number_of_occasions_not_doing_preferred_duties')
if args.add4:
    not_preferred = {}
    not_preferred_P = {}
    not_preferred_A = {}
    not_preferred_SB = {}
    for s in all_s:
        for e in all_e:
            not_preferred[(s, e)] = model.NewBoolVar('Not_doing_preferred_duties_%s_%s' % (s, e))
            not_preferred_P[(s, e)] = model.NewBoolVar('Not_doing_preferred_duties_PRO_%s_%s' % (s, e))
            not_preferred_A[(s, e)] = model.NewBoolVar('Not_doing_preferred_duties_ARO_%s_%s' % (s, e))
            not_preferred_SB[(s, e)] = model.NewBoolVar('Not_doing_preferred_duties_Safety_Boat_%s_%s' % (s, e))

            model.Add(not_preferred_P[(s, e)] == P[(s, e)] - P_PRO[s]).OnlyEnforceIf(P[(s, e)])
            model.Add(not_preferred_P[(s, e)] == 0).OnlyEnforceIf(P[(s, e)].Not())
            
            model.Add(not_preferred_A[(s, e)] == A[(s, e)] - P_ARO[s]).OnlyEnforceIf(A[(s, e)])
            model.Add(not_preferred_A[(s, e)] == 0).OnlyEnforceIf(A[(s, e)].Not())
            
            test = model.NewBoolVar('')
            model.Add(SB_1[(s, e)] + SB_2[(s, e)] == 1).OnlyEnforceIf(test)
            model.Add(SB_1[(s, e)] + SB_2[(s, e)] == 0).OnlyEnforceIf(test.Not())
            model.Add(not_preferred_SB[(s, e)] == SB_1[(s, e)] + SB_2[(s, e)] - P_SB[s]).OnlyEnforceIf(test)
            model.Add(not_preferred_SB[(s, e)] == 0).OnlyEnforceIf(test.Not())

            model.Add(not_preferred[(s, e)] == not_preferred_P[(s, e)] + not_preferred_A[(s, e)] + not_preferred_SB[(s, e)])
    model.Add(num_not_preferred == sum(not_preferred[(s, e)] for e in all_e for s in all_s))

'''---------- Find maximum and minimum number of duties allocated ----------'''

duty_s = {}
for s in all_s:
    duty_s[s] = model.NewIntVar(0, len(all_e), 'Number_of_duties_in_all_series_%s' % s)
    model.Add(duty_s[s] == sum(D[(s, e)] for e in all_e))

max_val = model.NewIntVar(0, len(all_e), 'max_val')
model.AddMaxEquality(max_val, [duty_s[s] for s in all_s])
min_val = model.NewIntVar(0, len(all_e), 'min_val')
model.AddMinEquality(min_val, [duty_s[s] for s in all_s])

'''---------- Objective ----------'''

model.Minimize(len(all_s) * len(all_e) * 3 * (max_val - min_val) + num_not_preferred)

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
            print('  Event %i' % (e+1))
            for s in self._all_s:
                is_playing = True
                if self.Value(self._P[(s, e)]):
                    is_playing = False
                    print('    Sailor %i works as PRO' % (s+1))
                if self.Value(self._A[(s, e)]):
                    is_playing = False
                    print('    Sailor %i works as ARO' % (s+1))
                if self.Value(self._SB_1[(s, e)]):
                    is_playing = False
                    print('    Sailor %i works on a safety boat as a helmer' % (s+1))
                if self.Value(self._SB_2[(s, e)]):
                    is_playing = False
                    print('    Sailor %i works on a safety boat as a crewer' % (s+1))

        print('Objective value: %i' % self.ObjectiveValue())
        print('Not preferred: %i' % self.Value(num_not_preferred))
        print('Max duties: %i' % self.Value(max_val))
        print('Min duties: %i' % self.Value(min_val))
        
        aver = sum(self.Value(duty_s[s]) for s in all_s) / len(all_s)
        print('Weighted average duties: %f' % aver)

        duty_f = {}
        for s in all_s:
            duty_f[s] = self.Value(duty_s[s])
        for s in sorted(duty_f, key=duty_f.get, reverse=True):
            print('Sailor: %i Duties: %i' % (s, duty_f[s]))

        print('There are %i solutions.' % self._solution_count)

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
    print('Not preferred: %i' % solver.Value(num_not_preferred))
    print('Max duties: %i' % solver.Value(max_val))
    print('Min duties: %i' % solver.Value(min_val))
    
    aver = sum(solver.Value(duty_s[s]) for s in all_s) // len(all_s)
    print('Weighted average duties: %f' % aver)

    duty_o = {}
    for s in all_s:
        duty_o[s] = solver.Value(duty_s[s])
    for s in sorted(duty_o, key=duty_o.get, reverse=True):
        print('Sailor: %i Duties: %i' % (s, duty_o[s]))
elif status == cp_model.FEASIBLE:
    print('This problem has feasible solutions')
elif status == cp_model.INFEASIBLE:
    print('This problem has no solutions')
else:
    print('Error')