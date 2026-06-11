import pandas as pd
import matplotlib.pyplot as plt
import ast
from collections import Counter

import numpy as np
import ast
from illuminator.builder import ModelConstructor

class JusticeAgentController(ModelConstructor):
    """
    Justice Agent Controller for managing energy reciprocity.
    Analyzes global energy state (Gini, Usage Rate) and outputs 
    recommendations for each household based on per-house lists.
    """

    parameters = {
        'houses': 2,
        'alpha': 0.1,  # Production incentive coefficient
        'beta': 0.1,   # Consumption reduction coefficient
    }
    
    inputs = {
        'consumption': [], # Expecting a list from New_House_Type
        'production': []   # Expecting a list from New_House_Type
    }
    
    outputs = {
        'recommendations': [], # List of [action_name, [i_econ, i_soc, i_eco], coeff]
        'usage_rate': 0,
        'reciprocity_index': 0
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Maintaining exact structure as requested
        self.houses = self._model.parameters.get('houses', 2)
        self.alpha = self._model.parameters.get('alpha', 0.1)
        self.beta = self._model.parameters.get('beta', 0.1)
        

    def step(self, time: int, inputs: dict = None, max_advance: int = 900) -> int:
        # 1. Strip the outer 'time-based_0' wrapper if it exists
        # This is the "Aha!" moment from your logs
        actual_inputs = inputs.get('time-based_0', inputs) 
        
        print(f"\n[DEBUG STEP {time}] Actual Inputs: {actual_inputs.keys()}")

        # 2. Extract Consumption
        cons_data = actual_inputs.get('consumption', {})
        cons_in = self._unpack_mosaik_data(cons_data)
        
        # 3. Extract Production
        prod_data = actual_inputs.get('production', {})
        prod_in = self._unpack_mosaik_data(prod_data)

        # 4. Check and execute
        if not cons_in or not prod_in:
            print(f"  >> ERROR: Still no data. Raw structure: {actual_inputs}")
            return time + self._model.time_step_size

        results = self.calculate_justice_logic(cons_in, prod_in)
        self.set_outputs(results)

        return time + self._model.time_step_size

    def _unpack_mosaik_data(self, attr_dict):
        """Helper to reach through Neighborhood_A-0... -> 'value'"""
        if not attr_dict:
            return []
        
        try:
            # We get the first entity (Neighborhood_A)
            entity_id = list(attr_dict.keys())[0]
            # Your log shows: {'Neighborhood_A...': {'message_origin': 'output', 'value': [...]}}
            # So we need to access ['value']
            data_packet = attr_dict[entity_id]
            
            if isinstance(data_packet, dict) and 'value' in data_packet:
                return data_packet['value']
            return data_packet # Fallback if it's already the list
        except Exception as e:
            print(f"  >> Unpack Error: {e}")
            return []
    

    def _parse_list(self, data):
        """Helper to ensure input is a clean list of floats of length self.houses."""
        # Handle string serialization if it occurs
        if isinstance(data, str):
            try:
                data = ast.literal_eval(data)
            except:
                return [0.0] * self.houses
        
        # If it's just a single number (common at step 0), expand it to a list
        if isinstance(data, (int, float)):
            return [float(data)] * self.houses
            
        # Ensure the list matches the number of houses
        if isinstance(data, list):
            if len(data) == self.houses:
                return [float(x) for x in data]
            else:
                # Pad or trim to match house count
                return (list(data) + [0.0] * self.houses)[:self.houses]
        
        return [0.0] * self.houses

    def calculate_gini_index(self, cons_list, prod_list):
        """1 - Gini coefficient of [|prod_i - cons_i|]"""
        diffs = [abs(p - c) for p, c in zip(prod_list, cons_list)]
        n = len(diffs)
        # If all houses are perfectly balanced (diff=0), reciprocity is 1.0
        if n < 2 or sum(diffs) == 0: 
            return 1.0
        
        diffs = np.sort(diffs)
        index = np.arange(1, n + 1)
        gini = (np.sum((2 * index - n - 1) * diffs)) / (n * np.sum(diffs))
        return float(1 - gini)

    def get_recommendation_packet(self, target_group, dev_cons, dev_prod, house_id):
        """
        Maps deviation and target group to specific incentive weights.
        """
        res = ["No action", [0, 0, 0], 0]
        
        # Debugging Print: See exactly what the packet receives
        print(f"House {house_id} | Group: {target_group} | d_cons: {dev_cons:.2f} | d_prod: {dev_prod:.2f}")

        # PRIORITY 1: High Consumption (Outliers above 35% of mean)
        if dev_cons > 0.35:
            print(f"  >> Triggered High Cons for House {house_id}")
            if target_group == "receiver":
                return ["Reduce consumption", [1.0, 0.2, 1.0], 1.0]
            else:
                return ["Reduce consumption", [0.5, 0.5, 1.0], 1.0]

        # PRIORITY 2: Low Production (Negative Deviations)
        if dev_prod < -0.35:
            print(f"  >> Triggered Low Prod for House {house_id}")
            if target_group == "receiver":
                return ["Installing PV", [1.0, 0.5, 1.0], 1.0]
            else:
                return ["Installing PV", [0.5, 1.0, 0.5], 1.0]
                
        elif dev_prod < -0.15:
            print(f"  >> Triggered PV Subsidy for House {house_id}")
            return ["Subsidy for PV", [1.0, 0.8, 0.2], 0.5]

        # PRIORITY 3: Moderate Consumption issues (15% to 35% above mean)
        if 0.15 < dev_cons <= 0.35:
            print(f"  >> Triggered Penalty for House {house_id}")
            if target_group == "receiver":
                return ["Receive Penalty", [1.0, 1.0, 1.0], 0.5]
            else:
                return ["Receive Penalty", [0.5, 0.5, 0.5], 0.5]

        # PRIORITY 4: Minor adjustments
        if 0 < dev_cons <= 0.15:
            print(f"  >> Triggered Flex Cons for House {house_id}")
            return ["Flexible Consumption", [0.2, 1.0, 1.0], 0.25]
        
        if 0 < dev_prod <= 0.15:
            print(f"  >> Triggered Expand PV for House {house_id}")
            return ["Expand PV", [0.2, 1.0, 1.0], 0.25]

        print(f"  >> Result: NO ACTION for House {house_id}")
        return res

    def calculate_justice_logic(self, cons_list, prod_list) -> dict:
        sum_cons = sum(cons_list)
        sum_prod = sum(prod_list)
        m_cons = sum_cons / self.houses if self.houses > 0 else 0
        m_prod = sum_prod / self.houses if self.houses > 0 else 0
        
        usage_rate = float(sum_cons / sum_prod if sum_prod != 0 else 999)
        recip_idx = self.calculate_gini_index(cons_list, prod_list)
        
        print(f"\n--- Justice Step: Mean Cons: {m_cons:.2f}, Mean Prod: {m_prod:.2f}, Usage: {usage_rate:.2f} ---")
        
        recommendations = []

        for i in range(self.houses):
            p, c = prod_list[i], cons_list[i]
            d_cons = (c - m_cons) / m_cons if m_cons > 0 else 0
            d_prod = (p - m_prod) / m_prod if m_prod > 0 else 0
            
            # Simplified grouping to ensure we ALWAYS have a group
            if p < c:    target_group = "receiver"
            elif p > c:  target_group = "contributor"
            else:        target_group = "balanced"

            # Run recommendation
            rec = self.get_recommendation_packet(target_group, d_cons, d_prod, i)
            recommendations.append(rec)

        return {
            'recommendations': recommendations,
            'usage_rate': usage_rate,
            'reciprocity_index': recip_idx
        }
    
class New_House_Type(ModelConstructor):
    parameters = {
        'houses': 5,
        'alphas': [0.1, 0.5, 0.2, 0.8, 0.3],
        'betas': [0.05, 0.2, 0.1, 0.4, 0.1],
        'consumption': [2.5, 1.2, 3.8, 0.5, 2.0],
        'production': [0.8, 2.5, 0.0, 1.5, 0.5],
        'incentive_weights': [[0.5, 0.2, 0.3], [0.1, 0.1, 0.8], [0.5, 0.5, 0.0], [0.2, 0.2, 0.6], [0.4, 0.4, 0.2]], 
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
        'production': []   
    }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        params = self._model.parameters
        
        self.houses = params.get('houses', 5)
        self.alphas = params.get('alphas', [0.1] * self.houses)
        self.betas = params.get('betas', [0.1] * self.houses)
        
        # CRITICAL: Use list() to create a deep copy so we can modify it 
        # independently over time without referencing the static YAML params.
        self.base_consumption = list(params.get('consumption', [0.0] * self.houses))
        self.base_production = list(params.get('production', [0.0] * self.houses))
        
        self.incentive_weights = params.get('incentive_weights', [[1/3, 1/3, 1/3]] * self.houses)
        self.threshold = params.get('decision_threshold', 0.5)

        print(f"DEBUG INIT: Cons check: {self.base_consumption}")

    def step(self, time: int, inputs: dict = None, max_advance: int = 900) -> int:
        actual_inputs = inputs.get('time-based_0', inputs)
        
        # Extract recommendations from the mosaik-style input dictionary
        recs_dict = actual_inputs.get('recommendations', {})
        recs_list = []
        
        if recs_dict:
            # mosaik sends dicts keyed by entity ID. We grab the list from the first one.
            recs_list = list(recs_dict.values())[0]
            print(f"[HOUSE STEP {time}] Received {len(recs_list)} recommendations.")
        else:
            print(f"[HOUSE STEP {time}] NO recommendations found in inputs!")

        # Process the dynamics and set outputs for the collector
        results = self.calculate_household_dynamics(recs_list)
        self.set_outputs(results)

        return time + self._model.time_step_size

    def calculate_household_dynamics(self, recommendations) -> dict:
        individual_dem = []
        
        # --- FIXED EXTRACTION LOGIC ---
        if isinstance(recommendations, dict):
            # We now know specifically to look for the 'value' key
            if 'value' in recommendations:
                recommendations = recommendations['value']
            else:
                # Fallback in case mosaik nesting changes
                recommendations = next(iter(recommendations.values()))
        
        if isinstance(recommendations, str):
             print(f"[CRITICAL] Grabbed a string instead of a list: {recommendations}")
             recommendations = []
             
        if not isinstance(recommendations, list):
            recommendations = []
        # -------------------------------

        print(f"\n--- Processing {len(recommendations)} Recommendations ---")

        for i in range(self.houses):
            individual_dem.append(self.base_consumption[i])

            if i < len(recommendations):
                rec = recommendations[i]
                
                if isinstance(rec, list) and len(rec) == 3:
                    action_name, action_incentives, action_coeff = rec
                    
                    if action_name != "No action":
                        house_weights = self.incentive_weights[i]
                        score = sum(w * s for w, s in zip(house_weights, action_incentives))
                        
                        print(f"  House {i} | {action_name} | Score: {score:.2f} vs Thresh: {self.threshold}")

                        if score >= self.threshold:
                            name_lower = action_name.lower()
                            
                            # Match keywords for consumption reduction
                            if any(kw in name_lower for kw in ["cons", "reduce", "penalty"]):
                                old_val = self.base_consumption[i]
                                self.base_consumption[i] *= (1 - (action_coeff * self.alphas[i]))
                                print(f"    >>> ACCEPTED: {old_val:.2f} -> {self.base_consumption[i]:.2f}")
                            
                            # Match keywords for PV/Production
                            elif any(kw in name_lower for kw in ["pv", "install", "subsidy"]):
                                old_val = self.base_production[i]
                                self.base_production[i] *= (1 + (action_coeff * self.betas[i]))
                                print(f"    >>> ACCEPTED: Prod {old_val:.2f} -> {self.base_production[i]:.2f}")
                        else:
                            print(f"    xxx REJECTED: Score {score:.2f} too low.")
                    else:
                        print(f"  House {i} | Agent suggested 'No action'")
            
            # Final persistence
            self.base_consumption[i] = round(float(self.base_consumption[i]), 4)
            self.base_production[i] = round(float(self.base_production[i]), 4)

        return {
            'sum_load_dem': round(sum(individual_dem), 2),
            'sum_consumption': round(sum(self.base_consumption), 2),
            'sum_production': round(sum(self.base_production), 2),
            'consumption': list(self.base_consumption),
            'production': list(self.base_production)
        }
    
#######################
#_  PLOT FUNCTIONS   _#
#######################

def plot_neighborhood_energy(csv_path: str, neighborhood_prefix: str = 'Neighborhood_A') -> None:
    """
    Loads simulation data from a CSV, unpacks household list arrays, 
    and generates aligned consumption and production subplots against sequential months.
    """
    # 1. Load the data
    df = pd.read_csv(csv_path)

    # Reconstruct exact column names based on prefix
    cons_col = f'{neighborhood_prefix}.consumption'
    prod_col = f'{neighborhood_prefix}.production'

    # 2. Convert strings of lists into actual Python lists
    df[cons_col] = df[cons_col].apply(ast.literal_eval)
    df[prod_col] = df[prod_col].apply(ast.literal_eval)

    # 3. Expand the lists into separate columns for plotting
    cons_expanded = pd.DataFrame(df[cons_col].tolist(), index=df.index)
    prod_expanded = pd.DataFrame(df[prod_col].tolist(), index=df.index)

    # NEW: Create a clean numeric sequence for months starting at 1
    months_seq = range(1, len(df) + 1)

    # 4. Plotting setup
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)

    # Plot Consumption
    for i in range(cons_expanded.shape[1]):
        # CHANGE: plotted against months_seq instead of df['date']
        ax1.plot(months_seq, cons_expanded[i], marker='o', label=f'Household {i}')

    ax1.set_title(f'Household Consumption ({neighborhood_prefix})', fontsize=14)
    ax1.set_ylabel('Consumption (kWh)')
    ax1.legend(title="Households", loc='upper left', bbox_to_anchor=(1, 1))
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Plot Production
    for i in range(prod_expanded.shape[1]):
        # CHANGE: plotted against months_seq instead of df['date']
        ax2.plot(months_seq, prod_expanded[i], marker='s', linestyle='--', label=f'Household {i}')

    ax2.set_title(f'Household Production ({neighborhood_prefix})', fontsize=14)
    ax2.set_ylabel('Production (kWh)')
    
    # CHANGE: Updated x-axis label to represent sequential months
    ax2.set_xlabel('Months', fontsize=12) 
    ax2.legend(title="Households", loc='upper left', bbox_to_anchor=(1, 1))
    ax2.grid(True, linestyle='--', alpha=0.6)

    # CHANGE: Force matplotlib to only show integer steps on the x-axis
    import matplotlib.ticker as ticker
    ax2.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # No rotation needed anymore since they are small numbers!
    plt.tight_layout()
    plt.show()

import pandas as pd
import matplotlib.pyplot as plt
import ast
import matplotlib.ticker as ticker
from collections import Counter

def plot_justice_metrics(csv_path: str, controller_prefix: str = 'Justice_Controller') -> None:
    """
    Loads simulation data from a CSV, analyzes reciprocity trends, 
    parses recommendation tuples, and displays a combined metric/distribution plot
    against sequential month numbers.
    
    Parameters:
    -----------
    csv_path : str
        Path to the output CSV file (e.g., 'out_justice_test.csv')
    controller_prefix : str
        The naming prefix of your controller entity in the CSV (default: 'Justice_Controller')
    """
    # 1. Load data
    df = pd.read_csv(csv_path)

    # Reconstruct column names dynamically
    recs_col = f'{controller_prefix}.recommendations'
    recip_col = f'{controller_prefix}.reciprocity_index'

    # 2. Parse the recommendations column safely
    df[recs_col] = df[recs_col].apply(ast.literal_eval)

    all_recommendations = []
    for row in df[recs_col]:
        for rec in row:
            # rec structure expected: [action_name, [i_econ, i_soc, i_eco], coeff]
            all_recommendations.append(rec[0])

    rec_counts = Counter(all_recommendations)

    # NEW: Create a clean numeric sequence for months starting at 1
    months_seq = range(1, len(df) + 1)

    # 3. Plotting Setup
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), gridspec_kw={'width_ratios': [2, 1]})

    # --- Left Plot: Reciprocity Index ---
    # CHANGE: plotted against months_seq instead of df['date']
    ax1.fill_between(months_seq, df[recip_col], color='skyblue', alpha=0.3)
    ax1.plot(months_seq, df[recip_col], color='dodgerblue', lw=2, label='Reciprocity Index')

    ax1.set_title(f'Justice Metric: Reciprocity Index Over Time ({controller_prefix})', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Index Value')
    
    # CHANGE: Updated x-axis label to generic Months
    ax1.set_xlabel('Months', fontsize=12)
    ax1.set_ylim(0, 1.1) 
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend()

    # CHANGE: Force integer steps on the x-axis so you don't get decimal month markers
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # --- Right Plot: Recommendation Distribution ---
    actions = list(rec_counts.keys())
    counts = list(rec_counts.values())

    # Set up styling palette
    colors = ['#66b3ff', '#99ff99', '#ffcc99', '#ff9999', '#c2c2f0', '#ffb3e6']

    # Draw horizontal bars using only needed slices of the palette
    ax2.barh(actions, counts, color=colors[:len(actions)], edgecolor='black', alpha=0.8)
    ax2.set_title('Total Recommendations Sent', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Frequency (Count)')

    # Add numeric count text labels on top of the bars
    for i, v in enumerate(counts):
        ax2.text(v + 0.2, i, str(v), va='center', fontweight='bold')

    plt.tight_layout()
    plt.show()

    # --- Console Summary Output ---
    print(f"Total Individual Recommendations Processed: {len(all_recommendations)}")
    print("Action Breakdown:")
    for action, count in rec_counts.items():
        print(f"  - {action}: {count}")
