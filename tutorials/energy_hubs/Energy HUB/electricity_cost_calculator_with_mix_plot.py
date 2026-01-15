import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

def calculate_electricity_cost(
    price_file,
    consumption_file,
    consumption_column='Controller1.dump',
    consumption_date_column='date',
    price_date_column='MTU (CET/CEST)',
    price_column='Price (EUR/MWh)',
    # Optional renewable generation parameters
    pv_output_file=None,
    pv_column=None,
    wind_output_file=None,
    wind_column=None,
    new_settings=None,
    output_csv='./outputs/electricity_cost_results.csv'
):
    """
    Calculate electricity costs from consumption and prices.
    Optionally include renewable generation (PV, wind, battery).
    
    Parameters:
    -----------
    price_file : str
        Path to electricity price CSV (EUR/MWh)
    consumption_file : str
        Path to consumption CSV
    consumption_column : str
        Column name for consumption (kW)
    consumption_date_column : str
        Date column in consumption file
    price_date_column : str
        Date column in price file
    price_column : str
        Price column name (EUR/MWh)
    pv_output_file : str, optional
        Path to PV generation output file
    pv_column : str, optional
        Column name for PV power output (kW)
    wind_output_file : str, optional
        Path to wind generation output file
    wind_column : str, optional
        Column name for wind power output (kW)
    new_settings : dict, optional
        Settings with keys: 'n_pv', 'n_wind', 'battery_capacity_kWh'
    output_csv : str
        Output file path
    
    Returns:
    --------
    pd.DataFrame
        Results with costs
    """
    
    # print("="*70)
    # print("ELECTRICITY COST CALCULATION")
    # print("="*70)
    
    # Component costs
    BATTERY_COST_EUR_PER_KWH = 600
    PV_COST_EUR_EACH = 800
    WIND_COST_EUR_PER_KWH = 0.07
    
    # Load main files
    # print("\nLoading price and consumption files...")
    prices = pd.read_csv(price_file)
    consumption = pd.read_csv(consumption_file)
    
    # print(f"✓ Price data: {len(prices)} rows")
    # print(f"✓ Consumption data: {len(consumption)} rows")
    
    # Parse consumption dates
    consumption[consumption_date_column] = pd.to_datetime(consumption[consumption_date_column])
    consumption_start = consumption[consumption_date_column].min()
    
    # print(f"\nConsumption starts at: {consumption_start}")
    
    # Align price file dates to consumption
    # print("\nAligning price file dates to consumption dates...")
    first_price_entry = prices[price_date_column].iloc[0]
    
    # Check if price data has intervals or single timestamps
    if ' - ' in first_price_entry:
        # Interval format
        price_start_str = first_price_entry.split(' - ')[0]
        price_start = pd.to_datetime(price_start_str, format='%d/%m/%Y %H:%M:%S')
        
        # Shift price intervals
        time_diff = consumption_start - price_start
        new_price_dates = []
        for interval in prices[price_date_column]:
            parts = interval.split(' - ')
            start = pd.to_datetime(parts[0], format='%d/%m/%Y %H:%M:%S')
            end = pd.to_datetime(parts[1], format='%d/%m/%Y %H:%M:%S')
            new_start = start + time_diff
            new_end = end + time_diff
            new_interval = f"{new_start.strftime('%d/%m/%Y %H:%M:%S')} - {new_end.strftime('%d/%m/%Y %H:%M:%S')}"
            new_price_dates.append(new_interval)
        prices[price_date_column] = new_price_dates
        
        # Extract start timestamps for matching
        prices['timestamp'] = pd.to_datetime(
            prices[price_date_column].str.split(' - ').str[0],
            format='%d/%m/%Y %H:%M:%S'
        )
    else:
        # Single timestamp format
        prices['timestamp'] = pd.to_datetime(prices[price_date_column])
        time_diff = consumption_start - prices['timestamp'].min()
        prices['timestamp'] = prices['timestamp'] + time_diff
    
    # print(f"✓ Price dates aligned")
    
    # Prepare consumption
    consumption.set_index(consumption_date_column, inplace=True)
    consumption['Consumption_kW'] = consumption[consumption_column] * -1  # Convert negative to positive
    
    time_hours = 0.25  # 15 minutes
    consumption['Energy_MWh'] = consumption['Consumption_kW'] * time_hours / 1000
    
    # Prepare price data
    prices.set_index('timestamp', inplace=True)
    prices['Price_EUR_MWh'] = pd.to_numeric(prices[price_column], errors='coerce')
    
    # Join consumption and prices
    result = consumption.join(prices['Price_EUR_MWh'], how='inner')
    
    # print(f"✓ Matched {len(result)} timesteps")
    
    if len(result) == 0:
        print("⚠ WARNING: No timestamps matched!")
        return None
    
    # Calculate baseline cost (without renewables)
    result['Grid_Energy_MWh'] = result['Energy_MWh']
    result['Grid_Cost_EUR'] = result['Grid_Energy_MWh'] * result['Price_EUR_MWh']
    result['PV_Cost_EUR'] = 0
    result['Wind_Cost_EUR'] = 0
    result['Cost_EUR'] = result['Grid_Cost_EUR']
    
    # Initialize renewable generation columns
    result['PV_Energy_MWh'] = 0
    result['Wind_Energy_MWh'] = 0
    result['Net_Energy_MWh'] = result['Energy_MWh']
    
    # Track capital costs
    capital_costs = {
        'pv': 640,
        'wind': 0,
        'battery': 0,
        'total': 0
    }
    
    # Load and process renewable generation if provided
    renewable_available = False
    
    if new_settings and any([pv_output_file, wind_output_file]):
        # print("\n" + "="*70)
        # print("PROCESSING RENEWABLE GENERATION")
        # print("="*70)
        
        n_pv = new_settings.get('n_pv', 0)
        n_wind = new_settings.get('n_wind', 0)
        battery_capacity = new_settings.get('battery_capacity_kWh', 0)
        
        # print(f"Settings: {n_pv} PVs, {n_wind} wind turbines, {battery_capacity} kWh battery")
        
        # Calculate capital costs
        if n_pv > 0:
            capital_costs['pv'] = n_pv * PV_COST_EUR_EACH
        if battery_capacity > 0:
            capital_costs['battery'] = battery_capacity * BATTERY_COST_EUR_PER_KWH
        capital_costs['total'] = capital_costs['pv'] + capital_costs['wind'] + capital_costs['battery']
        
        # Load PV generation
        if pv_output_file and os.path.exists(pv_output_file) and n_pv > 0:
            # print(f"\nLoading PV generation from {pv_output_file}...")
            try:
                pv_data = pd.read_csv(pv_output_file)
                pv_data[consumption_date_column] = pd.to_datetime(pv_data[consumption_date_column])
                pv_data.set_index(consumption_date_column, inplace=True)
                
                # Join with result
                result = result.join(pv_data[[pv_column]], how='left', rsuffix='_pv')
                result['PV_kW'] = result[pv_column].fillna(0) * -1  # Convert negative to positive
                result['PV_Energy_MWh'] = result['PV_kW'] * time_hours / 1000
                renewable_available = True
                # print(f"✓ PV data loaded")
            except Exception as e:
                print(f"⚠ Could not load PV data: {e}")
        
        # Load wind generation
        if wind_output_file and os.path.exists(wind_output_file) and n_wind > 0:
            # print(f"\nLoading wind generation from {wind_output_file}...")
            try:
                wind_data = pd.read_csv(wind_output_file)
                wind_data[consumption_date_column] = pd.to_datetime(wind_data[consumption_date_column])
                wind_data.set_index(consumption_date_column, inplace=True)
                
                # Join with result
                result = result.join(wind_data[[wind_column]], how='left', rsuffix='_wind')
                result['Wind_kW'] = wind_data[wind_column].fillna(0) * -1  # Convert negative to positive
                result['Wind_Energy_MWh'] = result['Wind_kW'] * time_hours / 1000
                
                # Calculate wind cost
                result['Wind_Cost_EUR'] = result['Wind_Energy_MWh'] * 1000 * WIND_COST_EUR_PER_KWH  # Convert MWh to kWh
                capital_costs['wind'] = result['Wind_Cost_EUR'].sum()
                capital_costs['total'] = capital_costs['pv'] + capital_costs['wind'] + capital_costs['battery']
                
                renewable_available = True
                # print(f"✓ Wind data loaded")
            except Exception as e:
                print(f"⚠ Could not load wind data: {e}")
        
        if renewable_available:
            # Calculate net energy from grid (consumption - renewables)
            result['Total_Renewable_MWh'] = result['PV_Energy_MWh'] + result['Wind_Energy_MWh']
            result['Net_Energy_MWh'] = result['Energy_MWh'] - result['Total_Renewable_MWh']
            result['Net_Energy_MWh'] = result['Net_Energy_MWh'].clip(lower=0)  # Can't be negative
            
            # Calculate costs by source
            result['Grid_Energy_MWh'] = result['Net_Energy_MWh']
            result['Grid_Cost_EUR'] = result['Grid_Energy_MWh'] * result['Price_EUR_MWh']
            
            # PV cost is just capital cost (amortized per timestep for plotting purposes)
            if 'PV_Energy_MWh' in result.columns and result['PV_Energy_MWh'].sum() > 0:
                pv_cost_per_timestep = capital_costs['pv'] / len(result) if capital_costs['pv'] > 0 else 0
                result['PV_Cost_EUR'] = pv_cost_per_timestep
            
            # Wind has operational cost
            if 'Wind_Cost_EUR' in result.columns:
                # Wind cost already calculated during loading
                pass
            
            # Total cost includes grid + wind operational costs
            result['Cost_EUR'] = result['Grid_Cost_EUR'] + result.get('Wind_Cost_EUR', 0)
    
    # Calculate cumulative costs
    result['Cumulative_Cost_EUR'] = result['Cost_EUR'].cumsum()
    
    # Calculate statistics
    # print("\n" + "="*70)
    # print("COST SUMMARY")
    # print("="*70)
    
    total_energy_consumed = result['Energy_MWh'].sum()
    total_cost = result['Cost_EUR'].sum()
    cumulative_cost_final = result['Cumulative_Cost_EUR'].iloc[-1]
    mean_cost = result['Cost_EUR'].mean()
    peak_cost = result['Cost_EUR'].max()
    mean_price = result['Price_EUR_MWh'].mean()
    
    print(f"\nBASELINE (Grid only):")
    print(f"  Total Energy Consumed:    {total_energy_consumed:.2f} MWh")
    print(f"  Total Cost:               €{total_cost:,.2f}")
    # print(f"  Cumulative Cost (final):  €{cumulative_cost_final:,.2f}")
    # print(f"  Average Cost per step:    €{mean_cost:.2f}")
    # print(f"  Peak Cost in a step:      €{peak_cost:.2f}")
    print(f"  Mean Price:               €{mean_price:.2f}/MWh")
    
    if renewable_available:
        total_renewable = result['Total_Renewable_MWh'].sum()
        total_grid_with_renewable = result['Grid_Energy_MWh'].sum()
        renewable_percentage = (total_renewable / total_energy_consumed) * 100 if total_energy_consumed > 0 else 0
        
        print(f"\nWITH RENEWABLES:")
        print(f"  PV Generation:            {result['PV_Energy_MWh'].sum():.2f} MWh")
        print(f"  Wind Generation:          {result['Wind_Energy_MWh'].sum():.2f} MWh")
        print(f"  Total Renewable:          {total_renewable:.2f} MWh ({renewable_percentage:.1f}%)")
        print(f"  Grid Energy (net):        {total_grid_with_renewable:.2f} MWh")
        print(f"  Operational Cost:         €{total_cost:,.2f}")
        
        print(f"\nCAPITAL COSTS:")
        if capital_costs['pv'] > 0:
            print(f"  PV Installation:          €{capital_costs['pv']:,.2f}")
        if capital_costs['wind'] > 0:
            print(f"  Wind Turbines:            €{capital_costs['wind']:,.2f}")
        if capital_costs['battery'] > 0:
            print(f"  Battery Storage:          €{capital_costs['battery']:,.2f}")
        print(f"  Total Capital Cost:       €{capital_costs['total']:,.2f}")
        print(f"  Total Cost (Opex+Capex):  €{total_cost + capital_costs['total']:,.2f}")
    
    print(f"\nNumber of timesteps:        {len(result)}")
    print("="*70)
    
    # Save results
    result.to_csv(output_csv)
    print(f"\n✓ Results saved to: {output_csv}")
    
    return result


def plot_electricity_cost(result_df, title='Electricity Cost Breakdown Over Time'):
    """
    Plot electricity costs as a stacked area chart showing grid vs renewable costs.
    
    Parameters:
    -----------
    result_df : pd.DataFrame
        Results from calculate_electricity_cost()
    title : str
        Plot title
    """
    if result_df is None or len(result_df) == 0:
        print("No data to plot!")
        return
    
    print("\n" + "="*70)
    print("PLOTTING ELECTRICITY COST BREAKDOWN")
    print("="*70)
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    
    # Check if we have renewable data
    has_renewables = 'PV_Cost_EUR' in result_df.columns and 'Wind_Cost_EUR' in result_df.columns
    
    if has_renewables and (result_df['PV_Cost_EUR'].sum() > 0 or result_df['Wind_Cost_EUR'].sum() > 0):
        # Stacked area chart with cost breakdown
        
        # Prepare data for stacking
        grid_cost = result_df['Grid_Cost_EUR'].fillna(0)
        pv_cost = result_df['PV_Cost_EUR'].fillna(0)
        wind_cost = result_df['Wind_Cost_EUR'].fillna(0)
        
        # Create stacked area plot
        ax.fill_between(result_df.index, 0, grid_cost, 
                       label='Grid Cost', alpha=0.7, color='#ff7f0e')
        ax.fill_between(result_df.index, grid_cost, grid_cost + wind_cost, 
                       label='Wind Cost (operational)', alpha=0.7, color='#2ca02c')
        ax.fill_between(result_df.index, grid_cost + wind_cost, 
                       grid_cost + wind_cost + pv_cost, 
                       label='PV Cost (amortized)', alpha=0.7, color='#1f77b4')
        
        # Add total cost line on top
        total_cost = grid_cost + wind_cost + pv_cost
        ax.plot(result_df.index, total_cost, 
               linewidth=2, color='black', label='Total Cost', alpha=0.8, linestyle='--')
        
        # Calculate percentages for legend
        total_grid = grid_cost.sum()
        total_wind = wind_cost.sum()
        total_pv = pv_cost.sum()
        total_all = total_grid + total_wind + total_pv
        
        if total_all > 0:
            grid_pct = (total_grid / total_all) * 100
            wind_pct = (total_wind / total_all) * 100
            pv_pct = (total_pv / total_all) * 100
            
            # Update legend with percentages
            handles, labels = ax.get_legend_handles_labels()
            labels[0] = f'Grid Cost ({grid_pct:.1f}%)'
            labels[1] = f'Wind Cost ({wind_pct:.1f}%)'
            labels[2] = f'PV Cost ({pv_pct:.1f}%)'
            ax.legend(handles, labels, loc='best', fontsize=11, framealpha=0.9)
        else:
            ax.legend(loc='best', fontsize=11, framealpha=0.9)
    else:
        # Just plot grid cost (no renewables)
        ax.plot(result_df.index, result_df['Cost_EUR'], 
                linewidth=1.5, color='#ff7f0e', label='Grid Cost')
        ax.fill_between(result_df.index, result_df['Cost_EUR'], 
                         alpha=0.3, color='#ff7f0e')
        
        mean_cost = result_df['Cost_EUR'].mean()
        ax.axhline(y=mean_cost, color='orange', linestyle='--', 
                   linewidth=2, label=f'Mean: €{mean_cost:.2f}', alpha=0.8)
        ax.legend(loc='best', fontsize=11, framealpha=0.9)
    
    ax.set_xlabel('Time', fontsize=13, fontweight='bold')
    ax.set_ylabel('Cost (EUR)', fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.show()
    
    print("✓ Plot displayed")


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================

if __name__ == "__main__":
    # BASELINE - No renewables
    print("SCENARIO 1: BASELINE (Grid only)")
    print("="*70)
    
    results_baseline = calculate_electricity_cost(
        price_file='electricity_prices.csv',
        consumption_file='your_consumption_file.csv',
        consumption_column='Controller1.dump',
        consumption_date_column='date',
        price_date_column='MTU (CET/CEST)',
        price_column='Price (EUR/MWh)',
        output_csv='./outputs/electricity_cost_baseline.csv'
    )
    
    if results_baseline is not None:
        plot_electricity_cost(results_baseline, title='Electricity Cost - Baseline (Grid Only)')
    
    # WITH RENEWABLES (if files exist)
    print("\n\nSCENARIO 2: WITH RENEWABLES")
    print("="*70)
    
    new_settings = {
        'n_pv': 10,              # Number of PV panels
        'n_wind': 5,             # Number of wind turbines
        'battery_capacity_kWh': 100  # Battery capacity in kWh
    }
    
    results_renewable = calculate_electricity_cost(
        price_file='electricity_prices.csv',
        consumption_file='your_consumption_file.csv',
        consumption_column='Controller1.dump',
        consumption_date_column='date',
        price_date_column='MTU (CET/CEST)',
        price_column='Price (EUR/MWh)',
        pv_output_file='pv_generation.csv',  # Optional
        pv_column='PV_power_kW',              # Optional
        wind_output_file='wind_generation.csv',  # Optional
        wind_column='Wind_power_kW',            # Optional - USE YOUR ACTUAL COLUMN NAME
        new_settings=new_settings,
        output_csv='./outputs/electricity_cost_with_renewables.csv'
    )
    
    if results_renewable is not None:
        plot_electricity_cost(results_renewable, title='Electricity Cost - With Renewables')
