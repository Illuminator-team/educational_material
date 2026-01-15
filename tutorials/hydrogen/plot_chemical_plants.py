import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def plot_chemical_plants_demand(csv_file='chemical_plants_data.csv', save_fig=False, filename='chemical_plants_energy_demand.png'):
    """
    Plot total energy demand (electricity and heat) for chemical plants.
    
    Parameters:
    -----------
    csv_file : str
        Path to the CSV file containing chemical plant data
    save_fig : bool
        Whether to save the figure as a file (default: False)
    filename : str
        Name of the output file if save_fig is True
    
    Returns:
    --------
    fig, ax : matplotlib figure and axis objects
    """
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Calculate total electricity demand (Power + Cooling)
    df['Total_Electricity_MW'] = df['Power_MW'] + df['Cooling_MW']
    
    # Calculate total heat demand (LPS + MPS + HPS)
    df['Total_Heat_MW'] = df['LPS_MW'] + df['MPS_MW'] + df['HPS_MW']
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Set up the bar positions
    x = np.arange(len(df))
    width = 0.35
    
    # Create bars for electricity and heat
    bars1 = ax.bar(x - width/2, df['Total_Electricity_MW'], width, 
                   label='Electricity (Power + Cooling)', color='#3498db', alpha=0.8)
    bars2 = ax.bar(x + width/2, df['Total_Heat_MW'], width, 
                   label='Heat (LPS + MPS + HPS)', color='#e74c3c', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('Chemical Plant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Energy Demand [MW]', fontsize=12, fontweight='bold')
    ax.set_title('Total Energy Demand by Chemical Plant\n(Electricity vs Heat)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df['Chemical_plant'], rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    # Add value labels on top of bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:  # Only show label if value is non-zero
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}',
                       ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if save_fig:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
    
    return fig, ax



class ScenarioPlotter:
    def __init__(self):
        self.results_history = []
    
    def add_and_plot(self, energy_price, co2_emission, scenario_name):
        """
        Add new scenario results and update the plot.
        """
        
        
        # Append current results
        self.results_history.append({
            'scenario': scenario_name,
            'energy_price': energy_price,
            'co2_emission': co2_emission
        })
        
        # Extract data for plotting
        scenarios = [r['scenario'] for r in self.results_history]
        energy_prices = [r['energy_price'] for r in self.results_history]
        co2_emissions = [r['co2_emission'] for r in self.results_history]
        
        # Create figure with two subplots
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot energy prices
        ax1.plot(range(len(energy_prices)), energy_prices, 'o-', linewidth=2, markersize=8)
        ax1.set_xlabel('Scenario Number')
        ax1.set_ylabel('Energy Price')
        ax1.set_title('Energy Prices Across Scenarios')
        ax1.set_xticks(range(len(scenarios)))
        ax1.set_xticklabels(scenarios, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Plot CO2 emissions
        ax2.plot(range(len(co2_emissions)), co2_emissions, 'o-', linewidth=2, markersize=8, color='red')
        ax2.set_xlabel('Scenario Number')
        ax2.set_ylabel('CO2 Emissions')
        ax2.set_title('CO2 Emissions Across Scenarios')
        ax2.set_xticks(range(len(scenarios)))
        ax2.set_xticklabels(scenarios, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def reset(self):
        """Reset the history for a new set of scenarios."""
        self.results_history = []