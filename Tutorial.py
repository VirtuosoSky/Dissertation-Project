# Importing librabries

from ortools.sat.python import cp_model

# Data

num_nurses = 4
num_shifts = 3
num_days = 3
all_nurses = range(num_nurses)
all_shifts = range(num_shifts)
all_days = range(num_days)

# Creating model

model = cp_model.CpModel()

# Creating variables

shifts = {}
for n in all_nurses:
    for d in all_days:
        for s in all_shifts:
            shifts[(n, d, s)] = model.NewBoolVar('shift_n%id%is%i' % (n, d, s))
# print(shifts)

# Assigning shift to nurse condition 1

for d in all_days:
    for s in all_shifts:
        model.AddExactlyOne(shifts[(n, d, s)] for n in all_nurses)

# Assigning shift to nurse condition 2

for n in all_nurses:
    for d in all_days:
        model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

# Assigning shifts evenly

min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
if num_shifts * num_days % num_nurses == 0:
    max_shifts_per_nurse = min_shifts_per_nurse
else:
    max_shifts_per_nurse = min_shifts_per_nurse + 1

for n in all_nurses:
    num_shifts_worked = []
    for d in all_days:
        for s in all_shifts:
            num_shifts_worked.append(shifts[(n, d, s)])
    model.Add(min_shifts_per_nurse <= sum(num_shifts_worked))
    model.Add(sum(num_shifts_worked) <= max_shifts_per_nurse)

# Solver parameter update

solver = cp_model.CpSolver()
solver.parameters.linearization_level = 0

# Enumerate all solutions

solver.parameters.enumerate_all_solutions = True

# Register a callback

class NursesPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    '''Print intermediate solutions'''

    def __init__(self, shifts, num_nurses, num_days, num_shifts, limit):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._shifts = shifts
        self._num_nurses = num_nurses
        self._num_days = num_days
        self._num_shifts = num_shifts
        self._solution_count = 0
        self._solution_limit = limit
    
    def on_solution_callback(self):
        
        print('Solution %i' % self._solution_count)
        self._solution_count += 1
        for d in range(self._num_days):
            print('Day %i' % d)
            for n in range(self._num_nurses):
                is_working = False
                for s in range(self._num_shifts):
                    if self.Value(self._shifts[(n, d, s)]):
                        is_working = True
                        print('  Nurse %i works shift %i' % (n, s))
                if not is_working:
                    print('  Nurse {} does not work'.format(n))
        
        if self._solution_count >= self._solution_limit:
            print('  Stop search after %i solutions' % self._solution_limit)
            self.StopSearch()
    
    def solution_count(self):
        return self._solution_count
    
# Display the first five solutions

solution_limit = 5
solution_printer = NursesPartialSolutionPrinter(shifts, num_nurses, num_days, num_shifts, solution_limit)

# Launch a solver

solver.Solve(model, solution_printer)


