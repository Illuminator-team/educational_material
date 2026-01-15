import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

def calculate_renewable_and_grid_costs(
    price_file,
    consumption_file,
    renewable_output_file,
    consumption_column='Controller1.dump',
    consumption_date_column='date',
    price_date_column='MTU (CET/CEST)',
    price_column='Day-ahead Price (EUR/MWh)',
    pv_column='PV1.pv',
    wind_column='Wind1.wind_gen',
    # Renewable system parameters
    n_pv=0,
    n_wind=0,
    battery_capacity_kWh=0,
    # LCOE parameters for renewables
    pv_cost_per_panel_EUR=800,
    pv_capacity_per_panel_kW=0.4,  # 400W panels
    pv_lifetime_years=25,
    wind_cost_per_turbine_EUR=50000,
    wind_capacity_per_turbine_kW=10,  # 10 kW turbines
    wind_lifetime_years=20,
    battery_cost_per_kWh_EUR=600,
    battery_lifetime_years=10,
    discount_rate=0.05,  # 5% discount rate
    output_csv='./outputs/renewable_grid_cost_results.csv'
):
    """
    Calculate electricity costs separating:
    1. Grid electricity costs (based on market prices)
    2. Renewable electricity costs (based on LCOE)
    
    Returns detailed cost breakdown and energy sources for each timestep.
    
    Parameters:
    -----------
    price_file : str
        Path to electricity price CSV (EUR/MWh)
    consumption_file : str
        Path to consumption CSV (contains grid consumption after renewables)
    renewable_output_file : str
        Path to renewable generation output file (out_Tutorial_RES_Bat.csv)
    consumption_column : str
        Column name for grid consumption (kW) - this is the net grid draw
    pv_column : str
        Column name for PV power output (kW)
    wind_column : str
        Column name for wind power output (kW)
    n_pv : int
        Number of PV panels
    n_wind : int
        Number of wind turbines
    battery_capacity_kWh : float
        Battery capacity in kWh
    pv_cost_per_panel_EUR : float
        Capital cost per PV panel
    wind_cost_per_turbine_EUR : float
        Capital cost per wind turbine
    battery_cost_per_kWh_EUR : float
        Capital cost per kWh of battery
    discount_rate : float
        Discount rate for LCOE calculation
    output_csv : str
        Output file path
    
    Returns:
    --------
    pd.DataFrame
        Results with costs broken down by source
    """
    
    print("="*80)
    print("RENEWABLE AND GRID ELECTRICITY COST CALCULATION")
    print("="*80)
    
    # Load data files
    print("\nLoading data files...")
    prices = pd.read_csv(price_file)
    consumption = pd.read_csv(consumption_file)
    renewables = pd.read_csv(renewable_output_file)
    
    print(f"✓ Price data: {len(prices)} rows")
    print(f"✓ Consumption data: {len(consumption)} rows")
    print(f"✓ Renewable generation data: {len(renewables)} rows")
    
    # Parse dates
    consumption[consumption_date_column] = pd.to_datetime(consumption[consumption_date_column])
    renewables[consumption_date_column] = pd.to_datetime(renewables[consumption_date_column])
    consumption_start = consumption[consumption_date_column].min()
    
    print(f"\nConsumption starts at: {consumption_start}")
    
    # Align price file dates to consumption
    print("\nAligning price file dates to consumption dates...")
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
    
    print(f"✓ Price dates aligned")
    
    # ===========================================================================
    # CALCULATE LCOE FOR RENEWABLES
    # ===========================================================================
    print("\n" + "="*80)
    print("CALCULATING LEVELIZED COST OF ENERGY (LCOE)")
    print("="*80)
    
    def calculate_lcoe(capital_cost, annual_generation_kWh, lifetime_years, discount_rate, om_cost_annual=0):
        """Calculate LCOE in EUR/kWh"""
        if annual_generation_kWh == 0:
            return 0
        
        # Present value of costs
        pv_costs = capital_cost
        for year in range(1, lifetime_years + 1):
            pv_costs += om_cost_annual / ((1 + discount_rate) ** year)
        
        # Present value of generation
        pv_generation = 0
        for year in range(1, lifetime_years + 1):
            pv_generation += annual_generation_kWh / ((1 + discount_rate) ** year)
        
        lcoe = pv_costs / pv_generation
        return lcoe
    
    # Time resolution
    time_hours = 0.25  # 15 minutes
    
    # Prepare renewable data
    renewables.set_index(consumption_date_column, inplace=True)
    
    # Validate columns exist
    print("\nValidating column names...")
    available_cols = renewables.columns.tolist()
    
    if pv_column not in available_cols:
        print(f"\n❌ ERROR: PV column '{pv_column}' not found!")
        print(f"\nAvailable columns in {renewable_output_file}:")
        for col in available_cols:
            print(f"  - {col}")
        print("\n💡 TIP: Use inspect_columns.py to find correct column names")
        print("Or run: python inspect_columns.py")
        return None
    
    if wind_column not in available_cols:
        print(f"\n❌ ERROR: Wind column '{wind_column}' not found!")
        print(f"\nAvailable columns in {renewable_output_file}:")
        for col in available_cols:
            print(f"  - {col}")
        print("\n💡 TIP: Use inspect_columns.py to find correct column names")
        print("Or run: python inspect_columns.py")
        return None
    
    print(f"✓ PV column '{pv_column}' found")
    print(f"✓ Wind column '{wind_column}' found")
    
    # Get PV and wind generation (convert negative to positive if needed)
    renewables['PV_kW'] = renewables[pv_column].abs()
    renewables['Wind_kW'] = renewables[wind_column].abs()
    renewables['PV_Energy_kWh'] = renewables['PV_kW'] * time_hours
    renewables['Wind_Energy_kWh'] = renewables['Wind_kW'] * time_hours
    
    # Calculate annual generation for LCOE
    # Annualize based on simulation period
    simulation_days = (renewables.index.max() - renewables.index.min()).days
    if simulation_days > 0:
        annualization_factor = 365.25 / simulation_days
    else:
        annualization_factor = 1
    
    total_pv_generation_kWh = renewables['PV_Energy_kWh'].sum()
    total_wind_generation_kWh = renewables['Wind_Energy_kWh'].sum()
    
    annual_pv_generation_kWh = total_pv_generation_kWh * annualization_factor
    annual_wind_generation_kWh = total_wind_generation_kWh * annualization_factor
    
    print(f"\nSimulation period: {simulation_days} days")
    print(f"Annualization factor: {annualization_factor:.2f}")
    
    # Calculate capital costs
    pv_capital_cost = n_pv * pv_cost_per_panel_EUR
    wind_capital_cost = n_wind * wind_cost_per_turbine_EUR
    battery_capital_cost = battery_capacity_kWh * battery_cost_per_kWh_EUR
    total_capital_cost = pv_capital_cost + wind_capital_cost + battery_capital_cost
    
    print(f"\n--- CAPITAL COSTS ---")
    if n_pv > 0:
        print(f"PV System ({n_pv} panels):           €{pv_capital_cost:,.2f}")
    if n_wind > 0:
        print(f"Wind System ({n_wind} turbines):      €{wind_capital_cost:,.2f}")
    if battery_capacity_kWh > 0:
        print(f"Battery ({battery_capacity_kWh} kWh):         €{battery_capital_cost:,.2f}")
    print(f"TOTAL CAPITAL COST:                €{total_capital_cost:,.2f}")
    
    # Calculate LCOE for each technology
    pv_lcoe_eur_per_kwh = 0
    wind_lcoe_eur_per_kwh = 0
    
    if n_pv > 0 and annual_pv_generation_kWh > 0:
        pv_om_annual = pv_capital_cost * 0.01  # 1% of capex per year
        pv_lcoe_eur_per_kwh = calculate_lcoe(
            pv_capital_cost,
            annual_pv_generation_kWh,
            pv_lifetime_years,
            discount_rate,
            pv_om_annual
        )
        print(f"\n--- PV LCOE ---")
        print(f"Annual generation:                 {annual_pv_generation_kWh:,.0f} kWh/year")
        print(f"Lifetime:                          {pv_lifetime_years} years")
        print(f"LCOE:                              €{pv_lcoe_eur_per_kwh:.4f}/kWh")
        print(f"                                   €{pv_lcoe_eur_per_kwh * 1000:.2f}/MWh")
    
    if n_wind > 0 and annual_wind_generation_kWh > 0:
        wind_om_annual = wind_capital_cost * 0.025  # 2.5% of capex per year
        wind_lcoe_eur_per_kwh = calculate_lcoe(
            wind_capital_cost,
            annual_wind_generation_kWh,
            wind_lifetime_years,
            discount_rate,
            wind_om_annual
        )
        print(f"\n--- WIND LCOE ---")
        print(f"Annual generation:                 {annual_wind_generation_kWh:,.0f} kWh/year")
        print(f"Lifetime:                          {wind_lifetime_years} years")
        print(f"LCOE:                              €{wind_lcoe_eur_per_kwh:.4f}/kWh")
        print(f"                                   €{wind_lcoe_eur_per_kwh * 1000:.2f}/MWh")
    
    # Battery LCOE (allocated proportionally to PV and wind)
    battery_lcoe_allocation = 0
    if battery_capacity_kWh > 0:
        # Battery cost is allocated to renewable generation
        battery_om_annual = battery_capital_cost * 0.02  # 2% of capex per year
        total_renewable_annual_kWh = annual_pv_generation_kWh + annual_wind_generation_kWh
        if total_renewable_annual_kWh > 0:
            battery_lcoe_allocation = calculate_lcoe(
                battery_capital_cost,
                total_renewable_annual_kWh,
                battery_lifetime_years,
                discount_rate,
                battery_om_annual
            )
            print(f"\n--- BATTERY STORAGE LCOE ---")
            print(f"Battery capacity:                  {battery_capacity_kWh} kWh")
            print(f"Lifetime:                          {battery_lifetime_years} years")
            print(f"LCOE (allocated):                  €{battery_lcoe_allocation:.4f}/kWh")
            print(f"                                   €{battery_lcoe_allocation * 1000:.2f}/MWh")
    
    # Adjust LCOE to include battery costs
    pv_lcoe_total = pv_lcoe_eur_per_kwh + battery_lcoe_allocation
    wind_lcoe_total = wind_lcoe_eur_per_kwh + battery_lcoe_allocation
    
    print(f"\n--- TOTAL LCOE (Including Battery) ---")
    if n_pv > 0:
        print(f"PV Total LCOE:                     €{pv_lcoe_total:.4f}/kWh (€{pv_lcoe_total * 1000:.2f}/MWh)")
    if n_wind > 0:
        print(f"Wind Total LCOE:                   €{wind_lcoe_total:.4f}/kWh (€{wind_lcoe_total * 1000:.2f}/MWh)")
    
    # ===========================================================================
    # CALCULATE TIMESTEP COSTS
    # ===========================================================================
    print("\n" + "="*80)
    print("CALCULATING TIMESTEP COSTS")
    print("="*80)
    
    # Prepare consumption data (grid draw)
    consumption.set_index(consumption_date_column, inplace=True)
    consumption['Grid_kW'] = consumption[consumption_column].abs()  # Grid consumption
    consumption['Grid_Energy_kWh'] = consumption['Grid_kW'] * time_hours
    
    # Prepare price data
    prices.set_index('timestamp', inplace=True)
    prices['Price_EUR_per_MWh'] = pd.to_numeric(prices[price_column], errors='coerce')
    prices['Price_EUR_per_kWh'] = prices['Price_EUR_per_MWh'] / 1000
    
    # Merge all data
    result = consumption[['Grid_kW', 'Grid_Energy_kWh']].copy()
    result = result.join(renewables[['PV_kW', 'Wind_kW', 'PV_Energy_kWh', 'Wind_Energy_kWh']], how='inner')
    result = result.join(prices['Price_EUR_per_kWh'], how='inner')
    
    print(f"✓ Matched {len(result)} timesteps")
    
    if len(result) == 0:
        print("⚠ WARNING: No timestamps matched!")
        return None
    
    # Calculate costs for each energy source
    result['PV_Cost_EUR'] = result['PV_Energy_kWh'] * pv_lcoe_total
    result['Wind_Cost_EUR'] = result['Wind_Energy_kWh'] * wind_lcoe_total
    result['Grid_Cost_EUR'] = result['Grid_Energy_kWh'] * result['Price_EUR_per_kWh']
    
    # Total cost per timestep
    result['Total_Cost_EUR'] = result['PV_Cost_EUR'] + result['Wind_Cost_EUR'] + result['Grid_Cost_EUR']
    
    # Calculate total demand (for reference)
    result['Total_Demand_kWh'] = result['Grid_Energy_kWh'] + result['PV_Energy_kWh'] + result['Wind_Energy_kWh']
    
    # Calculate cumulative costs
    result['Cumulative_Grid_Cost_EUR'] = result['Grid_Cost_EUR'].cumsum()
    result['Cumulative_PV_Cost_EUR'] = result['PV_Cost_EUR'].cumsum()
    result['Cumulative_Wind_Cost_EUR'] = result['Wind_Cost_EUR'].cumsum()
    result['Cumulative_Total_Cost_EUR'] = result['Total_Cost_EUR'].cumsum()
    
    # ===========================================================================
    # SUMMARY STATISTICS
    # ===========================================================================
    print("\n" + "="*80)
    print("COST SUMMARY")
    print("="*80)
    
    total_demand = result['Total_Demand_kWh'].sum()
    total_grid = result['Grid_Energy_kWh'].sum()
    total_pv = result['PV_Energy_kWh'].sum()
    total_wind = result['Wind_Energy_kWh'].sum()
    
    total_grid_cost = result['Grid_Cost_EUR'].sum()
    total_pv_cost = result['PV_Cost_EUR'].sum()
    total_wind_cost = result['Wind_Cost_EUR'].sum()
    total_operational_cost = result['Total_Cost_EUR'].sum()
    
    renewable_fraction = (total_pv + total_wind) / total_demand * 100 if total_demand > 0 else 0
    
    print(f"\n--- ENERGY SUPPLY ---")
    print(f"Total Demand:                      {total_demand:,.2f} kWh")
    print(f"  From Grid:                       {total_grid:,.2f} kWh ({total_grid/total_demand*100:.1f}%)")
    print(f"  From PV:                         {total_pv:,.2f} kWh ({total_pv/total_demand*100:.1f}%)")
    print(f"  From Wind:                       {total_wind:,.2f} kWh ({total_wind/total_demand*100:.1f}%)")
    print(f"Renewable Fraction:                {renewable_fraction:.1f}%")
    
    print(f"\n--- OPERATIONAL COSTS (Simulation Period) ---")
    print(f"Grid Electricity Cost:             €{total_grid_cost:,.2f}")
    print(f"PV Electricity Cost (LCOE):        €{total_pv_cost:,.2f}")
    print(f"Wind Electricity Cost (LCOE):      €{total_wind_cost:,.2f}")
    print(f"TOTAL OPERATIONAL COST:            €{total_operational_cost:,.2f}")
    
    avg_grid_price = result['Price_EUR_per_kWh'].mean() * 1000
    print(f"\nAverage Grid Price:                €{avg_grid_price:.2f}/MWh")
    
    # Calculate average cost per kWh by source
    if total_grid > 0:
        avg_grid_cost_per_kwh = total_grid_cost / total_grid
        print(f"Average Grid Cost:                 €{avg_grid_cost_per_kwh:.4f}/kWh")
    if total_pv > 0:
        print(f"PV LCOE:                           €{pv_lcoe_total:.4f}/kWh")
    if total_wind > 0:
        print(f"Wind LCOE:                         €{wind_lcoe_total:.4f}/kWh")
    
    if total_demand > 0:
        blended_operational_cost_per_kwh = total_operational_cost / total_demand
        print(f"Blended Cost (operational):        €{blended_operational_cost_per_kwh:.4f}/kWh")
    
    print(f"\n--- TOTAL COSTS (Operational + Capital) ---")
    print(f"Capital Costs:                     €{total_capital_cost:,.2f}")
    print(f"Operational Costs:                 €{total_operational_cost:,.2f}")
    print(f"TOTAL COST:                        €{total_operational_cost + total_capital_cost:,.2f}")
    
    if total_demand > 0:
        blended_total_cost_per_kwh = (total_operational_cost + total_capital_cost) / total_demand
        print(f"Blended Cost (total):              €{blended_total_cost_per_kwh:.4f}/kWh")
    
    print(f"\nNumber of timesteps:               {len(result)}")
    print("="*80)
    
    # Save results
    result.to_csv(output_csv)
    print(f"\n✓ Results saved to: {output_csv}")
    
    # Store metadata for plotting
    result.attrs['pv_lcoe'] = pv_lcoe_total
    result.attrs['wind_lcoe'] = wind_lcoe_total
    result.attrs['capital_costs'] = total_capital_cost
    
    return result


def plot_renewable_mix_costs(result_df, title='Electricity Cost Breakdown by Source'):
    """
    Create a stacked area plot showing electricity costs separated by source.
    Properly handles negative grid costs by:
    1. Stacking PV and wind costs (always positive)
    2. Adding positive grid costs on top
    3. Shading renewable costs that are compensated by negative grid costs
    4. Showing negative grid pricing as a separate indicator
    
    Parameters:
    -----------
    result_df : pd.DataFrame
        Results from calculate_renewable_and_grid_costs()
    title : str
        Plot title
    """
    if result_df is None or len(result_df) == 0:
        print("No data to plot!")
        return
    
    print("\n" + "="*80)
    print("PLOTTING RENEWABLE MIX ELECTRICITY COSTS")
    print("="*80)
    
    fig, axes = plt.subplots(2, 1, figsize=(16, 10))
    
    # ========== PLOT 1: STACKED COST PER TIMESTEP WITH NEGATIVE PRICING ==========
    ax1 = axes[0]
    
    # Separate positive and negative grid costs
    grid_cost_positive = result_df['Grid_Cost_EUR'].clip(lower=0)
    grid_cost_negative = result_df['Grid_Cost_EUR'].clip(upper=0)
    
    # Calculate renewable cost stack (always positive)
    renewable_base = result_df['Wind_Cost_EUR']
    renewable_total = result_df['Wind_Cost_EUR'] + result_df['PV_Cost_EUR']
    
    # Plot base renewable costs (Wind)
    ax1.fill_between(result_df.index, 0, renewable_base,
                     alpha=0.7, color='#17becf', label='Wind (LCOE)')
    
    # Plot PV costs on top of Wind
    ax1.fill_between(result_df.index, renewable_base, renewable_total,
                     alpha=0.7, color='#ff7f0e', label='PV (LCOE)')
    
    # Plot positive grid costs on top of renewables
    ax1.fill_between(result_df.index, renewable_total, 
                     renewable_total + grid_cost_positive,
                     alpha=0.7, color='#d62728', label='Grid Cost (buying)')
    
    # Calculate the compensation area (where negative grid cost offsets renewable cost)
    # This shows which part of renewable costs is compensated by selling to grid
    compensation = grid_cost_negative.abs()  # Make positive for visualization
    compensated_top = renewable_total
    compensated_bottom = (renewable_total + grid_cost_negative).clip(lower=0)
    
    # Shade the compensated area (where renewables are offset by negative pricing)
    ax1.fill_between(result_df.index, compensated_bottom, compensated_top,
                     where=(grid_cost_negative < 0),
                     alpha=0.4, color='green', 
                     label='Renewable cost offset by grid sales',
                     interpolate=True, hatch='///')
    
    # Plot negative grid pricing as a separate area below zero
    ax1.fill_between(result_df.index, 0, grid_cost_negative,
                     alpha=0.5, color='#2ca02c', 
                     label='Grid revenue (selling)', interpolate=True)
    
    # Add total cost line (the actual net cost)
    total_cost_line = renewable_total + result_df['Grid_Cost_EUR']
    ax1.plot(result_df.index, total_cost_line, 
            linewidth=2.5, color='black', alpha=0.8, label='Net Total Cost', linestyle='--')
    
    # Add a zero line for reference
    ax1.axhline(y=0, color='gray', linestyle='-', linewidth=1, alpha=0.5)
    
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Cost (EUR)', fontsize=12, fontweight='bold')
    ax1.set_title(title + ' - Per Timestep (with negative pricing)', fontsize=14, fontweight='bold', pad=15)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='upper left', fontsize=9, framealpha=0.9, ncol=2)
    
    # ========== PLOT 2: STACKED ENERGY GENERATION ==========
    ax2 = axes[1]
    
    # Create stacked area plot for energy
    ax2.fill_between(result_df.index, 0, result_df['Wind_Energy_kWh'],
                     alpha=0.7, color='#17becf', label='Wind')
    ax2.fill_between(result_df.index, 
                     result_df['Wind_Energy_kWh'], 
                     result_df['Wind_Energy_kWh'] + result_df['PV_Energy_kWh'],
                     alpha=0.7, color='#ff7f0e', label='PV')
    ax2.fill_between(result_df.index,
                     result_df['Wind_Energy_kWh'] + result_df['PV_Energy_kWh'],
                     result_df['Total_Demand_kWh'],
                     alpha=0.7, color='#d62728', label='Grid')
    
    # Add total demand line
    ax2.plot(result_df.index, result_df['Total_Demand_kWh'], 
            linewidth=2, color='black', alpha=0.6, label='Total Demand', linestyle='--')
    
    ax2.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Energy (kWh)', fontsize=12, fontweight='bold')
    ax2.set_title('Energy Supply Mix - Per Timestep', fontsize=14, fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='upper left', fontsize=10, framealpha=0.9)
    
    plt.tight_layout()
    
    # Save to current directory (works on all platforms)
    output_file = './outputs/renewable_mix_costs.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved to: {output_file}")
    
    plt.show()
    
    # Print statistics about negative pricing
    negative_periods = (result_df['Grid_Cost_EUR'] < 0).sum()
    total_negative_value = grid_cost_negative.sum()
    print(f"\n📊 Negative Pricing Statistics:")
    print(f"   Periods with negative pricing: {negative_periods}")
    print(f"   Total revenue from grid sales: €{abs(total_negative_value):.2f}")
    
    print("✓ Plots displayed")


def plot_cumulative_costs(result_df, title='Cumulative Electricity Costs'):
    """
    Plot cumulative costs over time, separated by source.
    
    Parameters:
    -----------
    result_df : pd.DataFrame
        Results from calculate_renewable_and_grid_costs()
    title : str
        Plot title
    """
    if result_df is None or len(result_df) == 0:
        print("No data to plot!")
        return
    
    print("\n" + "="*80)
    print("PLOTTING CUMULATIVE COSTS")
    print("="*80)
    
    fig, ax = plt.subplots(1, 1, figsize=(16, 8))
    
    # Plot cumulative costs by source
    ax.plot(result_df.index, result_df['Cumulative_Grid_Cost_EUR'], 
            linewidth=2.5, color='#d62728', label='Grid Electricity', alpha=0.8)
    ax.plot(result_df.index, result_df['Cumulative_Wind_Cost_EUR'], 
            linewidth=2.5, color='#17becf', label='Wind (LCOE)', alpha=0.8)
    ax.plot(result_df.index, result_df['Cumulative_PV_Cost_EUR'], 
            linewidth=2.5, color='#ff7f0e', label='PV (LCOE)', alpha=0.8)
    ax.plot(result_df.index, result_df['Cumulative_Total_Cost_EUR'], 
            linewidth=3, color='black', label='Total Cost', alpha=0.7, linestyle='--')
    
    ax.set_xlabel('Time', fontsize=13, fontweight='bold')
    ax.set_ylabel('Cumulative Cost (EUR)', fontsize=13, fontweight='bold')
    ax.set_title(title, fontsize=15, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    
    # Add capital cost reference line if available
    if hasattr(result_df, 'attrs') and 'capital_costs' in result_df.attrs:
        capital = result_df.attrs['capital_costs']
        ax.axhline(y=capital, color='purple', linestyle=':', 
                  linewidth=2, label=f'Capital Costs: €{capital:,.0f}', alpha=0.6)
        ax.legend(loc='upper left', fontsize=11, framealpha=0.9)
    
    plt.tight_layout()
    
    # Save to current directory (works on all platforms)
    output_file = './outputs/cumulative_costs.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved to: {output_file}")
    
    plt.show()
    
    print("✓ Plot displayed")


# ==============================================================================
# USAGE EXAMPLE
# ==============================================================================


    
    if results is not None:
        plot_renewable_mix_costs(results)
        plot_cumulative_costs(results)
