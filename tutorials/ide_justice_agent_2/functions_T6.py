import ast
from illuminator.builder import ModelConstructor

import pandas as pd
import matplotlib.pyplot as plt
import ast
import matplotlib.ticker as ticker
import matplotlib.patches as mpatches

class New_House_Type_Comm(ModelConstructor):
    parameters = {
        'houses': 5,
        'alphas': [0.1, 0.5, 0.2, 0.8, 0.3],
        'betas': [0.05, 0.2, 0.1, 0.4, 0.1],
        'consumption': [12.5, 1.2, 9.8, 0.5, 2.0],
        'production': [0.8, 2.5, 3.0, 1.5, 0.5],
        'incentive_weights': [[0.5, 0.2, 0.3]] * 5, 
        'decision_threshold': 0.5 
    }
    
    inputs = {
        'recommendations': [] 
    }
    
    outputs = {
        'sum_load_dem': 0,
        'sum_consumption': 0,
        'sum_production': 0,
        'consumption': [], 
        'production': [],
        'response': [] # Format: [[accepted_count, total_assigned_count], ...]
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        params = self._model.parameters
        self.houses = params.get('houses', 5)
        self.alphas = params.get('alphas', [0.1] * self.houses)
        self.betas = params.get('betas', [0.1] * self.houses)
        self.base_consumption = list(params.get('consumption', [0.0] * self.houses))
        self.base_production = list(params.get('production', [0.0] * self.houses))
        self.incentive_weights = params.get('incentive_weights', [[1/3]*3] * self.houses)
        self.threshold = params.get('decision_threshold', 0.5)

        # Trackers for System Checker
        self.accepted_count = [0] * self.houses
        self.assigned_count = [0] * self.houses

    def step(self, time: int, inputs: dict = None, max_advance: int = 900) -> int:
        actual_inputs = inputs.get('time-based_0', inputs)
        recs_dict = actual_inputs.get('recommendations', {})
        recs_list = self._unpack_mosaik_data(recs_dict)

        results = self.calculate_household_dynamics(recs_list)
        self.set_outputs(results)
        return time + self._model.time_step_size

    def _unpack_mosaik_data(self, attr_dict):
        if not attr_dict: return []
        entity_id = list(attr_dict.keys())[0]
        data_packet = attr_dict[entity_id]
        return data_packet.get('value', []) if isinstance(data_packet, dict) else data_packet

    def calculate_household_dynamics(self, recommendations) -> dict:
        individual_dem = list(self.base_consumption)

        for i in range(self.houses):
            if i < len(recommendations):
                rec = recommendations[i]
                if isinstance(rec, list) and len(rec) == 3:
                    action_name, action_incentives, action_coeff = rec
                    if action_name == "No action": continue

                    self.assigned_count[i] += 1
                    house_weights = self.incentive_weights[i]
                    score = sum(w * s for w, s in zip(house_weights, action_incentives))

                    if score >= self.threshold:
                        self.accepted_count[i] += 1
                        name_l = action_name.lower()
                        
                        # NEW LOGIC: Match flowchart action types
                        # Increase consumption: electrification, subsidy, access, appliance, incentive w
                        if any(kw in name_l for kw in ["electrif", "subsidy", "access", "appliance", "incentive w"]):
                            self.base_consumption[i] *= (1 + (action_coeff * self.alphas[i]))
                        
                        # Decrease consumption: reduce, penalty, flexible, efficiency, flex-enabling
                        elif any(kw in name_l for kw in ["reduce", "penalty", "flex", "efficien"]):
                            self.base_consumption[i] *= (1 - (action_coeff * self.alphas[i]))

                        # Production (if applicable)
                        elif "pv" in name_l or "install" in name_l:
                            self.base_production[i] *= (1 + (action_coeff * self.betas[i]))

            self.base_consumption[i] = round(float(self.base_consumption[i]), 4)

        return {
            'sum_load_dem': round(sum(individual_dem), 2),
            'sum_consumption': round(sum(self.base_consumption), 2),
            'sum_production': round(sum(self.base_production), 2),
            'consumption': list(self.base_consumption),
            'production': list(self.base_production),
            'response': [[self.accepted_count[i], self.assigned_count[i]] for i in range(self.houses)]
        }
    
import numpy as np
import ast
from illuminator.builder import ModelConstructor

from illuminator.builder import ModelConstructor

class JusticeAgentControllerCorridor(ModelConstructor):
    parameters = {
        'houses': 5,
        'sufficiency_floor': 5.0,
        'sufficiency_ceiling': 15.0,
        'capability_threshold': 0.5 # tau for mismatch check
    }
    
    inputs = {
        'consumption': [],
        'production': [],
        'response': []
    }
    
    outputs = {
        'recommendations': [],
        'hub_state': "Sufficiency",
        'usage_rate': 0,
        'capabilities': []  # Added capability tracking to outputs
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        params = self._model.parameters
        self.houses = params.get('houses', 5)
        self.floor = params.get('sufficiency_floor', 5.0)
        self.ceiling = params.get('sufficiency_ceiling', 15.0)
        self.tau = params.get('capability_threshold', 0.5)
        # Default starting capability is High
        self.capabilities = ["high"] * self.houses

    def step(self, time: int, inputs: dict = None, max_advance: int = 900) -> int:
        actual_inputs = inputs.get('time-based_0', inputs) 
        cons_in = self._unpack_mosaik_data(actual_inputs.get('consumption', {}))
        prod_in = self._unpack_mosaik_data(actual_inputs.get('production', {}))
        resp_in = self._unpack_mosaik_data(actual_inputs.get('response', {}))

        if not cons_in: 
            return time + self._model.time_step_size

        # 1. Update Capability via System Checker (R_i logic)
        if resp_in:
            for i, (accepted, assigned) in enumerate(resp_in):
                if assigned > 0:
                    r_i = accepted / assigned
                    # Flowchart: If High and R_i < tau -> Mismatch -> Nudge/Switch to Low
                    if self.capabilities[i] == "high" and r_i < self.tau:
                        self.capabilities[i] = "low"
                    elif self.capabilities[i] == "low" and r_i > self.tau:
                        self.capabilities[i] = "high"

        # 2. Determine Household States
        states = [] # -1: Below Floor, 0: Corridor, 1: Above Ceiling
        for c in cons_in:
            if c < self.floor: states.append(-1)
            elif c > self.ceiling: states.append(1)
            else: states.append(0)

        # 3. Determine Hub State
        n_below = states.count(-1)
        n_above = states.count(1)
        rbs = n_below / self.houses
        ras = n_above / self.houses

        hub_state = "Sufficiency"
        if rbs > 0 and ras == 0: hub_state = "Scarcity"
        elif rbs > 0 and ras > 0: hub_state = "Inequality"
        elif rbs == 0 and ras > 0: hub_state = "Extravagance"

        # 4. Generate Recommendations based on Flowchart branches
        recommendations = []
        for i in range(self.houses):
            rec = ["No action", [0,0,0], 0]
            status = states[i]
            cap = self.capabilities[i]

            # BRANCH: Check Energy Gap Below Sufficiency Floor
            if status == -1:
                dev = (self.floor - cons_in[i]) / self.floor
                if cap == "high":
                    if dev > 0.35: rec = ["Encourage beneficial electrification", [0.5, 0.5, 1.0], 0.3]
                    elif dev > 0: rec = ["Incentive w", [1.0, 0.5, 0.5], 0.15]
                else: # Low Capability
                    if dev > 0.35: rec = ["Provide energy subsidy", [1.0, 0.5, 0.5], 1.0]
                    elif dev > 0.15: rec = ["Provide efficient appliance support", [1.0, 0.5, 1.0], 0.5]
                    elif dev > 0: rec = ["Guaranteed community energy access", [1.0, 0.5, 0.5], 0.25]

            # BRANCH: Check Energy Gap Above Sufficiency Ceiling
            elif status == 1:
                dev = (cons_in[i] - self.ceiling) / self.ceiling
                if cap == "high":
                    if dev > 0.35: rec = ["Reduce consumption", [0.5, 0.5, 1.0], 1.0]
                    elif dev > 0.15: rec = ["Receive Penalty", [1.0, 0.5, 0.5], 0.5]
                    elif dev > 0: rec = ["Flexible Consumption", [0.5, 1.0, 0.5], 0.25]
                else: # Low Capability
                    if dev > 0.35: rec = ["Efficiency / infrastructure support", [0.5, 1.0, 0.5], 0.5]
                    elif dev > 0.15: rec = ["Flexibility-enabling upgrade", [0.5, 0.5, 0.5], 0.25]
                    elif dev > 0: rec = ["Light efficiency support", [0.5, 0, 1.0], 0.1]

            recommendations.append(rec)

        # Updated to include capability array tracking
        self.set_outputs({
            'recommendations': recommendations,
            'hub_state': hub_state,
            'usage_rate': sum(cons_in)/sum(prod_in) if sum(prod_in) > 0 else 0,
            'capabilities': list(self.capabilities)  # Export current snapshot
        })
        return time + self._model.time_step_size

    def _unpack_mosaik_data(self, attr_dict):
        if not attr_dict: return []
        entity_id = list(attr_dict.keys())[0]
        data = attr_dict[entity_id]
        return data.get('value', []) if isinstance(data, dict) else data
    
#######################
#_  PLOT FUNCTIONS   _#
#######################
    
def plot_neighborhood_energy(
    csv_path: str, 
    neighborhood_prefix: str = 'Neighborhood_A',
    floor: float = 40,
    ceiling: float = 140
) -> None:
    """
    Loads simulation data from a CSV, unpacks household consumption arrays, 
    and plots household trends against the Sufficiency Corridor boundaries.
    
    Parameters:
    -----------
    csv_path : str
        Path to the output CSV file
    neighborhood_prefix : str
        The naming prefix of your neighborhood entity in the CSV
    floor : float
        The sufficiency floor threshold (default from controller: 5.0)
    ceiling : float
        The sufficiency ceiling threshold (default from controller: 15.0)
    """
    # 1. Load the data
    df = pd.read_csv(csv_path)

    # Reconstruct exact column name based on prefix
    cons_col = f'{neighborhood_prefix}.consumption'

    # 2. Convert strings of lists into actual Python lists
    df[cons_col] = df[cons_col].apply(ast.literal_eval)

    # 3. Expand the lists into separate columns for plotting
    cons_expanded = pd.DataFrame(df[cons_col].tolist(), index=df.index)

    # Create a clean numeric sequence for months starting at 1
    months_seq = range(1, len(df) + 1)

    # 4. Plotting setup (Single plot layout now)
    fig, ax = plt.subplots(figsize=(12, 7))

    # --- Visualise the Sufficiency Corridor Shading ---
    # Shading the acceptable corridor zone
    ax.axhspan(floor, ceiling, color='green', alpha=0.10, label='Sufficiency Corridor Zone')
    
    # Boundary threshold lines
    ax.axhline(ceiling, color='firebrick', linestyle='--', lw=1.5, alpha=0.8, label=f'Ceiling ({ceiling} kWh)')
    ax.axhline(floor, color='darkorange', linestyle='--', lw=1.5, alpha=0.8, label=f'Floor ({floor} kWh)')

    # --- Plot Household Consumption ---
    for i in range(cons_expanded.shape[1]):
        ax.plot(months_seq, cons_expanded[i], marker='o', lw=2, label=f'Household {i}')

    # Formatting text, titles, labels
    ax.set_title(f'Household Consumption vs. Sufficiency Corridor ({neighborhood_prefix})', fontsize=14, fontweight='bold')
    ax.set_ylabel('Consumption (kWh)', fontsize=12)
    ax.set_xlabel('Months', fontsize=12) 
    
    # Pad y limits slightly outside thresholds to make sure visual spacing is clean
    ax.set_ylim(min(floor * 0.5, cons_expanded.min().min() * 0.9), 
                max(ceiling * 1.2, cons_expanded.max().max() * 1.1))

    # Layout adjustment and grids
    ax.legend(title="Indicators & Assets", loc='upper left', bbox_to_anchor=(1, 1))
    ax.grid(True, linestyle=':', alpha=0.5)

    # Force integer steps on x-axis
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    plt.tight_layout()
    plt.show()

def plot_justice_system_kpis(csv_path: str, controller_prefix: str = 'Justice_Controller') -> None:
    """
    Loads simulation data from a CSV, parses capability string states and system usage rates,
    and renders an aligned diagnostic timeline of multi-agent resilience.
    """
    # 1. Load data
    df = pd.read_csv(csv_path)
    
    cap_col = f'{controller_prefix}.capabilities'
    usage_col = f'{controller_prefix}.usage_rate'
    hub_col = f'{controller_prefix}.hub_state'
    
    # 2. Parse stringified arrays safely
    df[cap_col] = df[cap_col].apply(ast.literal_eval)
    
    # Convert 'high' -> 1 and 'low' -> 0 for numeric representation
    cap_numeric = []
    for row in df[cap_col]:
        cap_numeric.append([1 if c == 'high' else 0 for c in row])
    
    cap_df = pd.DataFrame(cap_numeric)
    steps = range(1, len(df) + 1)
    
    # 3. Plotting Setup
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 10), sharex=True)
    
    # --- Top Plot: Household Capabilities Tracker (Ridge / Track layout) ---
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i in range(cap_df.shape[1]):
        # Shift each household upward by an index multiplier so they have unique lanes
        lane_offset = i * 2 
        y_values = lane_offset + cap_df[i]
        
        # Step plot cleanly visualizes discrete state switches
        ax1.step(steps, y_values, where='mid', lw=2.5, marker='o', color=colors[i], label=f'Household {i}')
        
    ax1.set_title('Household Capability Status Timeline', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Vulnerability Tracker', fontsize=12)
    
    # Label the lanes cleanly on the Y-axis
    y_ticks = [i * 2 + 0.5 for i in range(cap_df.shape[1])]
    y_labels = [f'HH {i}' for i in range(cap_df.shape[1])]
    ax1.set_yticks(y_ticks)
    ax1.set_yticklabels(y_labels)
    ax1.grid(True, linestyle=':', alpha=0.5, axis='x')
    
    # Status Helper Text Box
    ax1.text(1.02, 0.85, 'State Within Lane:\n▲ Top = High Capability\n▼ Bottom = Low Capability', 
             transform=ax1.transAxes, fontsize=10, bbox=dict(facecolor='white', alpha=0.6, boxstyle='round'))
    ax1.legend(loc='upper left', bbox_to_anchor=(1.01, 0.7), title="Household Assets")

    # --- Bottom Plot: System Usage Rate & Shaded Hub States ---
    ax2.plot(steps, df[usage_col], color='darkmagenta', marker='s', lw=2.5, label='System Usage Rate')
    ax2.set_ylabel('Usage Rate (Total Cons / Prod)', fontsize=12)
    ax2.set_xlabel('Simulation Steps (Biweekly Intervals)', fontsize=12)
    ax2.set_title('Global Grid Performance & System State', fontsize=14, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # Dynamic background color configuration for hub states
    state_colors = {
        'Sufficiency': '#2ca02c',   # Green
        'Inequality': '#ffbb78',    # Warm Amber
        'Scarcity': '#d62728',      # Soft Red
        'Extravagance': '#aec7e8'  # Light Blue
    }
    
    # Shade background segments step by step
    unique_states = df[hub_col].unique()
    for idx, state in enumerate(df[hub_col]):
        ax2.axvspan(idx + 0.5, idx + 1.5, color=state_colors.get(state, '#grey'), alpha=0.15)
                    
    # Generate unified legend matching line data with background color patches
    legend_handles = [ax2.plot([], [], color='darkmagenta', marker='s', lw=2.5, label='Usage Rate')[0]]
    for state in unique_states:
        legend_handles.append(mpatches.Patch(color=state_colors.get(state, '#grey'), alpha=0.3, label=f'State: {state}'))
        
    ax2.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1, 1))
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    
    plt.tight_layout()
    plt.show()