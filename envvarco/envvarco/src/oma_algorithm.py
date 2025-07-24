import numpy as np
from pyvolt.nv_powerflow import solve  # Ensure nv_powerflow.solve is accessible in your project.

def shunt_reactor_objective_function(solution, system, shunt_reactor_reactive_power, base_apparent_power):
    # Convert solution values to binary (strict ON/OFF states)
    binary_solution = [1 if state >= 0.5 else 0 for state in solution]

    # Apply binary reactor states
    for idx, (node_name, reactor_reactive_power) in enumerate(shunt_reactor_reactive_power.items()):
        q_pu = -(binary_solution[idx] * reactor_reactive_power) / base_apparent_power  # Negative for reactive power absorption

        # Get the node
        node = system.get_node_by_uuid(node_name)
        if node:  # Check if node exists
            node.reactive_power = q_pu
        else:
            print(f"Warning: Node '{node_name}' not found in the system.")

    # Perform power flow analysis
    results_pf, _ = solve(system)
    voltages = {node.topology_node.name: abs(node.voltage_pu) for node in results_pf.nodes}

    # Objective 1: Voltage deviation (penalize deviations outside 0.95–1.00)
    voltage_deviation = sum([(max(v - 1.05, 0) + max(0.95 - v, 0)) ** 2 for v in voltages.values()])

    # Objective 2: Wear and tear (number of activated reactors)
    wear_and_tear = sum(binary_solution)

    return [voltage_deviation, wear_and_tear]


# Define capacitor-related objective functions
def capacitor_objective_function(solution, system, capacitor_reactive_power, base_apparent_power):
    # Convert solution values to binary (strict ON/OFF states)
    binary_solution = [1 if state >= 0.5 else 0 for state in solution]

    # Apply binary capacitor states
    for idx, (node_name, cap_reactive_power) in enumerate(capacitor_reactive_power.items()):
        q_pu = (binary_solution[idx] * cap_reactive_power) / base_apparent_power
        node = system.get_node_by_uuid(node_name)
        node.reactive_power = q_pu

    # Perform power flow analysis
    results_pf, _ = solve(system)
    voltages = {node.topology_node.name: abs(node.voltage_pu) for node in results_pf.nodes}

    # Objective 1: Voltage deviation (penalize deviations outside 1.00–1.05)
    voltage_deviation = sum([(max(v - 1.05, 0) + max(0.95 - v, 0)) ** 2 for v in voltages.values()])

    # Objective 2: Wear and tear (number of activated capacitors)
    wear_and_tear = sum(binary_solution)

    return [voltage_deviation, wear_and_tear]


# Pareto archive management
def update_pareto_archive(new_solution, archive):
    to_remove = []

    for idx, archived_solution in enumerate(archive):
        if dominates(archived_solution[-3:], new_solution[-3:]):  # Archived solution dominates new solution
            return archive  # Do not add new solution
        elif dominates(new_solution[-3:], archived_solution[-3:]):  # New solution dominates archived one
            to_remove.append(idx)

    # Remove dominated solutions from the archive
    archive = [archived_solution for i, archived_solution in enumerate(archive) if i not in to_remove]

    # Append the new solution to the archive
    archive.append(new_solution)
    return archive

# Dominance check
def dominates(obj1, obj2):
    return all(o1 <= o2 for o1, o2 in zip(obj1, obj2)) and any(o1 < o2 for o1, o2 in zip(obj1, obj2))

# Extract Pareto front
def extract_pareto_front(archive):
    non_dominated = []
    for solution in archive:
        dominated = False
        for other_solution in archive:
            if dominates(other_solution[-3:], solution[-3:]):
                dominated = True
                break
        if not dominated:
            non_dominated.append(solution)
    return non_dominated

# Fuzzy logic for selecting the best solution
def select_best_fuzzy(objectives):
    # Adjust weights for two objectives (voltage deviation, wear and tear)
    weights = np.array([0.95, 0.05])  # Voltage deviation is weighted higher than wear and tear
    f_min = objectives.min(axis=0)
    f_max = objectives.max(axis=0)

    # Avoid division by zero with a small epsilon value
    epsilon = 1e-6
    normalized_range = (f_max - f_min) + epsilon
    
    # Normalize membership values for the objectives
    membership_values = (f_max - objectives) / normalized_range
    
    # Compute fuzzy scores using weights
    fuzzy_scores = membership_values @ weights
    return np.argmax(fuzzy_scores)

# Initialization
def initialize_population(population_size, dimensions, lower_bounds, upper_bounds):
    return np.random.uniform(lower_bounds, upper_bounds, (population_size, dimensions))


def fungal_growth_optimizer(N, Tmax, ub, lb, dim, fobj):
    """
    Multi-objective Fungal Growth Optimizer (FGO) closely replicating MATLAB implementation.

    Parameters:
    - N: Population size.
    - Tmax: Maximum number of iterations.
    - ub: Upper bounds (list or array).
    - lb: Lower bounds (list or array).
    - dim: Dimension of the problem (number of decision variables).
    - fobj: Multi-objective function to evaluate solutions.

    Returns:
    - pareto_front: Final Pareto front of non-dominated solutions.
    - best_solution: Best solution selected using fuzzy logic.
    """
    # Initialize controlling parameters
    M = 0.6  # Trade-off between exploration and exploitation
    Ep = 0.7  # Probability of environmental effect
    R = 0.9  # Speed of convergence

    # Initialization
    S = np.random.uniform(lb, ub, (N, dim))  # Initial population
    pareto_archive = []  # Initialize Pareto archive

    print("HI")

    # Evaluate initial population and update Pareto archive
    for solution in S:
        objectives = fobj(solution)
        pareto_archive = update_pareto_archive(np.hstack((solution, objectives)), pareto_archive)

    t = 0  # Iteration counter

    while t < Tmax:
        # Allocate nutrients
        if t <= Tmax / 2:
            nutrients = np.random.rand(N)  # Exploration phase: random allocation
        else:
            nutrients = np.array([sol[-2] for sol in pareto_archive])  # Use Pareto front objectives
        nutrients = nutrients / (np.sum(nutrients) + 2 * np.random.rand())  # Normalize nutrients

        for i in range(N):
            # Randomly select three solutions for growth behavior
            a, b, c = np.random.choice([x for x in range(N) if x != i], size=3, replace=False)

            # Compute probability and exploration parameter
            p = (np.min(nutrients) - np.min(nutrients)) / (np.max(nutrients) - np.min(nutrients) + np.finfo(float).eps)
            Er = M + (1 - t / Tmax) * (1 - M)

            if p < Er:
                # Hyphal tip growth behavior
                F = (np.sum(nutrients) / np.sum(nutrients)) * np.random.rand() * (1 - t / Tmax) ** (1 - t / Tmax)
                E = np.exp(F)
                r1 = np.random.rand(dim)
                r2 = np.random.rand()
                U1 = r1 < r2
                S[i] = U1 * S[i] + (1 - U1) * (S[i] + E * (S[a] - S[b]))
            else:
                # Exploratory growth steps
                Ec = (np.random.rand(dim) - 0.5) * np.random.rand() * (S[a] - S[b])
                if np.random.rand() < np.random.rand():
                    De2 = np.random.rand(dim) * (S[i] - S[c]) * (np.random.rand(dim) > np.random.rand())
                    S[i] = S[i] + De2 * nutrients[i] + Ec * (np.random.rand() > np.random.rand())
                else:
                    De = np.random.rand() * (S[a] - S[i]) + np.random.rand(dim) * ((np.random.rand() > np.random.rand() * 2 - 1) * S[c] - S[i]) * (np.random.rand() > R)
                    S[i] = S[i] + De * nutrients[i] + Ec * (np.random.rand() > Ep)

            # Enforce bounds
            S[i] = np.clip(S[i], lb, ub)

            # Evaluate objectives
            objectives = fobj(S[i])

            # Update Pareto archive
            pareto_archive = update_pareto_archive(np.hstack((S[i], objectives)), pareto_archive)

        t += 1  # Increment iteration counter

        # Debugging: Print Pareto front at each iteration
        #print(f"\nIteration {t}: Pareto Front")
        pareto_front = extract_pareto_front(pareto_archive)
        for idx, sol in enumerate(pareto_front):
            decision_variables = sol[:-2]
            objectives = sol[-2:]
            #print(f"Solution {idx + 1}:")
            #print(f"  Capacitor States: {decision_variables}")
            #print(f"  Objectives: Voltage Deviation = {objectives[0]:.6f}, Wear and Tear = {objectives[1]:.6f}")

    # Extract Pareto front from archive
    pareto_front = extract_pareto_front(pareto_archive)

    # Select best solution using fuzzy logic
    objectives = np.array([sol[-2:] for sol in pareto_front])
    best_solution_index = select_best_fuzzy(objectives)
    best_solution = pareto_front[best_solution_index]

    # Return Pareto front and best solution
    return pareto_front, best_solution