import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime



def normalize_data(data):
    """
    Normalize data to 0-1 range using Min-Max normalization.
    
    Parameters:
    -----------
    data : pd.Series
        Data to normalize
    
    Returns:
    --------
    pd.Series
        Normalized data (0-1 range)
    """
    min_val = data.min()
    max_val = data.max()
    
    if max_val == min_val:
        return pd.Series(0, index=data.index)
    
    return (data - min_val) / (max_val - min_val)


def plot_combined_analysis(
    co2_results_file='co2_results.csv',
    cost_results_file='electricity_cost_results.csv',
    consumption_file='out_Tutorial_RES_Bat.csv',
    connection_cap=150,
    critical_limit=0.9,
    tolerance_limit=0.67,
    figsize=(14, 5)
):
    """
    Create two separate plots side by side:
    1. Left: CO2 emissions (normalized) with grid connection background
    2. Right: Electricity cost (normalized) with grid connection background
    
    Parameters:
    -----------
    co2_results_file : str
        Path to CO2 results CSV
    cost_results_file : str
        Path to electricity cost results CSV
    consumption_file : str
        Path to consumption file (for grid connection background)
    connection_cap : float
        Grid connection capacity (kW)
    critical_limit : float
        Critical limit fraction (0-1)
    tolerance_limit : float
        Tolerance limit fraction (0-1)
    figsize : tuple
        Figure size (width, height)
    
    Returns:
    --------
    fig, (ax1, ax2)
        Matplotlib figure and axes objects
    """
    
    # print("="*70)
    # print("COMBINED ANALYSIS: CO2 & COST WITH GRID CONNECTION")
    # print("="*70)
    
    # Load data
    # print("\nLoading data files...")
    co2_df = pd.read_csv(co2_results_file, index_col=0)
    co2_df.index = pd.to_datetime(co2_df.index)
    
    cost_df = pd.read_csv(cost_results_file, index_col=0)
    cost_df.index = pd.to_datetime(cost_df.index)
    
    consumption_df = pd.read_csv(consumption_file, index_col=0)
    consumption_df.index = pd.to_datetime(consumption_df.index)
    
    # Get load on connection
    load_on_connection = -consumption_df['Controller1.dump']
    
    # Check if Cost_EUR column exists, if not try to find it
    if 'Cost_EUR' not in cost_df.columns:
        print(f"Warning: 'Cost_EUR' column not found. Available columns: {cost_df.columns.tolist()}")
        # Try to find a cost column
        cost_columns = [col for col in cost_df.columns if 'cost' in col.lower() or 'eur' in col.lower() or 'price' in col.lower()]
        if cost_columns:
            cost_column = cost_columns[0]
            #print(f"Using column: {cost_column}")
            cost_df['Cost_EUR'] = cost_df[cost_column]
        else:
            print("ERROR: No cost column found!")
            return None, None
    
    # Check if we have Grid_Cost_EUR (the actual grid cost without renewables)
    if 'Grid_Cost_EUR' in cost_df.columns:
        #print("Using Grid_Cost_EUR (actual grid cost)")
        cost_df['Cost_EUR_Plot'] = cost_df['Grid_Cost_EUR'].clip(lower=0)
    else:
        # Use Cost_EUR but take absolute value for plotting
        # print("Using Cost_EUR")
        cost_df['Cost_EUR_Plot'] = cost_df['Cost_EUR'].abs()
    
    cost_df['Cost_EUR_Plot'] = cost_df['Cost_EUR_Plot'].fillna(0)
    
    # Normalize CO2 and cost data
    # print("Normalizing CO2 and cost data...")
    co2_normalized = normalize_data(co2_df['CO2_emissions_kg'])
    
    # Check for issues with cost data
    if cost_df['Cost_EUR_Plot'].max() == 0:
        print("WARNING: All cost values are zero!")
        cost_normalized = pd.Series(0, index=cost_df.index)
    else:
        cost_normalized = normalize_data(cost_df['Cost_EUR_Plot'])
    
    # Debug: Check the data ranges
    # print(f"CO2 original range: {co2_df['CO2_emissions_kg'].min():.2f} to {co2_df['CO2_emissions_kg'].max():.2f} kg")
    # print(f"Cost original range: €{cost_df['Cost_EUR_Plot'].min():.4f} to €{cost_df['Cost_EUR_Plot'].max():.4f}")
    # print(f"CO2 normalized range: {co2_normalized.min():.4f} to {co2_normalized.max():.4f}")
    # print(f"Cost normalized range: {cost_normalized.min():.4f} to {cost_normalized.max():.4f}")
    # print(f"Cost non-zero values: {(cost_df['Cost_EUR_Plot'] > 0).sum()} out of {len(cost_df)}")
    
    # Scale normalized data to fit in connection capacity range
    scale_factor = connection_cap * 0.95  # Use 85% of capacity for visibility
    co2_scaled = co2_normalized * scale_factor
    cost_scaled = cost_normalized * scale_factor
    
    # print(f"CO2 scaled range: {co2_scaled.min():.2f} to {co2_scaled.max():.2f}")
    # print(f"Cost scaled range: {cost_scaled.min():.2f} to {cost_scaled.max():.2f}")
    
    # Create figure with two subplots side by side
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, dpi=80, constrained_layout=True)
    
    # ========================================================================
    # LEFT PLOT: CO2 Emissions with Grid Connection Background
    # ========================================================================
    # print("Creating CO2 plot...")
    
    # Plot grid connection regions as background
    ax1.fill_between(x=load_on_connection.index, 
                     y1=(-critical_limit * connection_cap), 
                     y2=-connection_cap, 
                     color='#F02E31', alpha=0.4, label='Critical')
    ax1.fill_between(x=load_on_connection.index, 
                     y1=(critical_limit * connection_cap), 
                     y2=connection_cap, 
                     color='#F02E31', alpha=0.4)
    ax1.fill_between(x=load_on_connection.index, 
                     y1=-(tolerance_limit * connection_cap),
                     y2=-(critical_limit * connection_cap),
                     color='#FFE8A2', alpha=0.6, label='Tolerance')
    ax1.fill_between(x=load_on_connection.index, 
                     y1=(tolerance_limit * connection_cap), 
                     y2=(critical_limit * connection_cap),
                     color='#FFE8A2', alpha=0.6)
    ax1.fill_between(x=load_on_connection.index, 
                     y1=-(tolerance_limit * connection_cap),
                     y2=(tolerance_limit * connection_cap),
                     color='#DAF2D0', alpha=0.8, label='Good')
    
    # Plot load on connection (light gray for background)
    ax1.plot(load_on_connection.index, load_on_connection, 
             color='lightgray', linewidth=1.5, alpha=0.6, zorder=3, label='Load')
    ax1.hlines(y=0, xmin=min(load_on_connection.index), xmax=max(load_on_connection.index), 
               color='gray', linestyles='--', linewidth=1, zorder=2, alpha=0.5)
    
    # Plot normalized CO2 (scaled, prominent red line)
    ax1.plot(co2_normalized.index, co2_scaled, 
             color='#d62728', label='CO2 (normalized)', 
             linewidth=2.5, alpha=0.9, zorder=5)
    
    # Create secondary y-axis for actual CO2 values
    ax1_co2 = ax1.twinx()
    ax1_co2.plot(co2_df.index, co2_df['CO2_emissions_kg'],
                 color='#d62728', linewidth=0, alpha=0)  # Invisible line for axis scaling
    ax1_co2.set_ylabel('CO2 Emissions (kg)', fontsize=11, fontweight='bold', color='#d62728')
    ax1_co2.tick_params(axis='y', labelcolor='#d62728', labelsize=9)
    
    # Formatting
    ax1.set_xlabel('Time', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Load / Normalized Value (kW scale)', fontsize=11, fontweight='bold')
    ax1.set_title('CO2 Emissions with Grid Connection', 
                  fontsize=13, fontweight='bold', pad=12)
    ax1.set_xlim(min(load_on_connection.index), max(load_on_connection.index))
    ax1.set_ylim(-connection_cap, connection_cap)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M'))
    ax1.tick_params(axis='x', rotation=0, labelsize=9)
    ax1.tick_params(axis='y', labelsize=9)
    ax1.grid(True, alpha=0.3, linestyle='--', zorder=1)
    ax1.legend(loc='upper left', fontsize=8, framealpha=0.9)
    
    # ========================================================================
    # RIGHT PLOT: Electricity Cost with Grid Connection Background
    # ========================================================================
    # print("Creating Cost plot...")
    
    # Plot grid connection regions as background
    ax2.fill_between(x=load_on_connection.index, 
                     y1=(-critical_limit * connection_cap), 
                     y2=-connection_cap, 
                     color='#F02E31', alpha=0.4, label='Critical')
    ax2.fill_between(x=load_on_connection.index, 
                     y1=(critical_limit * connection_cap), 
                     y2=connection_cap, 
                     color='#F02E31', alpha=0.4)
    ax2.fill_between(x=load_on_connection.index, 
                     y1=-(tolerance_limit * connection_cap),
                     y2=-(critical_limit * connection_cap),
                     color='#FFE8A2', alpha=0.6, label='Tolerance')
    ax2.fill_between(x=load_on_connection.index, 
                     y1=(tolerance_limit * connection_cap), 
                     y2=(critical_limit * connection_cap),
                     color='#FFE8A2', alpha=0.6)
    ax2.fill_between(x=load_on_connection.index, 
                     y1=-(tolerance_limit * connection_cap),
                     y2=(tolerance_limit * connection_cap),
                     color='#DAF2D0', alpha=0.8, label='Good')
    
    # Plot load on connection (light gray for background)
    ax2.plot(load_on_connection.index, load_on_connection, 
             color='lightgray', linewidth=1.5, alpha=0.6, zorder=3, label='Load')
    ax2.hlines(y=0, xmin=min(load_on_connection.index), xmax=max(load_on_connection.index), 
               color='gray', linestyles='--', linewidth=1, zorder=2, alpha=0.5)
    
    # Plot normalized cost (scaled, prominent green line)
    ax2.plot(cost_normalized.index, cost_scaled, 
             color='#2ca02c', label='Cost (normalized)', 
             linewidth=2.5, alpha=0.9, zorder=5)
    
    # Create secondary y-axis for actual cost values
    ax2_cost = ax2.twinx()
    # Use the processed positive-only cost values for the axis
    ax2_cost.plot(cost_df.index, cost_df['Cost_EUR_Plot'],
                  color='#2ca02c', linewidth=0, alpha=0)  # Invisible line for axis scaling
    ax2_cost.set_ylabel('Grid Cost (€)', fontsize=11, fontweight='bold', color='#2ca02c')
    ax2_cost.tick_params(axis='y', labelcolor='#2ca02c', labelsize=9)
    
    # Formatting
    ax2.set_xlabel('Time', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Load / Normalized Value (kW scale)', fontsize=11, fontweight='bold')
    ax2.set_title('Electricity Cost with Grid Connection', 
                  fontsize=13, fontweight='bold', pad=12)
    ax2.set_xlim(min(load_on_connection.index), max(load_on_connection.index))
    ax2.set_ylim(-connection_cap, connection_cap)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d\n%H:%M'))
    ax2.tick_params(axis='x', rotation=0, labelsize=9)
    ax2.tick_params(axis='y', labelsize=9)
    ax2.grid(True, alpha=0.3, linestyle='--', zorder=1)
    ax2.legend(loc='upper left', fontsize=8, framealpha=0.9)
    
    # ========================================================================
    # Statistics Summary
    # ========================================================================
    # print("\n" + "="*70)
    # print("ANALYSIS SUMMARY")
    # print("="*70)
    
    # Calculate correlation
    correlation = co2_normalized.corr(cost_normalized)
    # print(f"\nCorrelation (CO2 vs Cost): {correlation:.4f}")
    
    # Check for grid congestion
    consumption_full = pd.read_csv(consumption_file)
    if 'Grid1.flag_warning' in consumption_full.columns:
        if (consumption_full["Grid1.flag_warning"] == 1).any():
            print("\n⚠ Grid congestion detected!")
            congestion_count = (consumption_full["Grid1.flag_warning"] == 1).sum()
            print(f"   Congestion events: {congestion_count}")
        else:
            print("\n✓ No grid congestion")
    
    # print("\nNORMALIZED VALUES (0-1 scale):")
    # print(f"  CO2  - Mean: {co2_normalized.mean():.4f}, Std: {co2_normalized.std():.4f}")
    # print(f"  Cost - Mean: {cost_normalized.mean():.4f}, Std: {cost_normalized.std():.4f}")
    """
    print("\nORIGINAL VALUES:")
    print(f"  CO2 Emissions - Mean: {co2_df['CO2_emissions_kg'].mean():.2f} kg, "
          f"Total: {co2_df['CO2_emissions_kg'].sum():.2f} kg")
    if 'Grid_Cost_EUR' in cost_df.columns:
        print(f"  Electricity Cost (Grid) - Mean: €{cost_df['Grid_Cost_EUR'].mean():.2f}, "
              f"Total: €{cost_df['Grid_Cost_EUR'].sum():.2f}")
    else:
        print(f"  Electricity Cost - Mean: €{cost_df['Cost_EUR_Plot'].mean():.2f}, "
              f"Total: €{cost_df['Cost_EUR_Plot'].sum():.2f}")
    print(f"  Grid Load - Mean: {load_on_connection.mean():.2f} kW, "
          f"Peak: {load_on_connection.abs().max():.2f} kW")
    
    print("="*70)
    """
    return fig, (ax1, ax2)


def save_combined_plot(
    output_file='combined_analysis.png',
    co2_results_file='co2_results.csv',
    cost_results_file='electricity_cost_results.csv',
    consumption_file='out_Tutorial_RES_Bat.csv',
    connection_cap=150,
    critical_limit=0.9,
    tolerance_limit=0.67,
    dpi=300
):
    """
    Generate and save the combined analysis plot.
    
    Parameters:
    -----------
    output_file : str
        Output file path (e.g., 'plot.png', 'plot.pdf')
    ... (other parameters same as plot_combined_analysis)
    dpi : int
        Resolution for saved figure
    """
    
    fig, axes = plot_combined_analysis(
        co2_results_file=co2_results_file,
        cost_results_file=cost_results_file,
        consumption_file=consumption_file,
        connection_cap=connection_cap,
        critical_limit=critical_limit,
        tolerance_limit=tolerance_limit
    )
    
    fig.savefig(output_file, dpi=dpi, bbox_inches='tight')
    # print(f"\n✓ Plot saved to: {output_file}")
    
    plt.show()
    
    return fig, axes


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================

if __name__ == "__main__":
    
    # print("CREATING COMBINED ANALYSIS PLOT")
    # print("Two plots: CO2 and Cost, both with grid connection background")
    # print("="*70)
    
    # Create the plots
    fig, axes = plot_combined_analysis(
        co2_results_file='co2_results.csv',
        cost_results_file='electricity_cost_results.csv',
        consumption_file='out_Tutorial_RES_Bat.csv',
        connection_cap=150,
        critical_limit=0.9,
        tolerance_limit=0.67,
        figsize=(14, 5)  # Adjust size as needed
    )
    
    plt.show()
    
    # Or save to file
    # save_combined_plot(output_file='combined_analysis.png')
