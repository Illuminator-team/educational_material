import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def align_dates_and_calculate_co2(
    generation_file = 'data\GENERATION_PER_TYPE_20251125-20251202.csv',
    consumption_file='out_Tutorial_5.csv',
    consumption_column='Controller1.dump',
    consumption_date_column='date',
    generation_date_column='MTU (CET/CEST)',
    output_csv='./co2_results.csv'

):
    """
    Complete workflow: align generation file dates to consumption file, calculate CO2, and plot.
    
    Parameters:
    -----------
    generation_file : str
        Path to generation CSV (with intervals like "DD/MM/YYYY HH:MM:SS - DD/MM/YYYY HH:MM:SS")
    consumption_file : str
        Path to consumption CSV (with single timestamps)
    consumption_column : str
        Column name for consumption data (kW)
    consumption_date_column : str
        Column name for dates in consumption file
    generation_date_column : str
        Column name for dates in generation file
    output_csv : str
        Where to save results
    
    Returns:
    --------
    pd.DataFrame
        Results with CO2 emissions
    """
    
    # print("="*70)
    # print("STEP 1: LOADING FILES")
    # print("="*70)
    
    # Load files
    generation = pd.read_csv(generation_file)
    consumption = pd.read_csv(consumption_file)
    
    # print(f"✓ Generation file loaded: {len(generation)} rows")
    # print(f"✓ Consumption file loaded: {len(consumption)} rows")
    
    # Emission factors (kg CO2 per MWh)
    emission_mapping = {
        'Biomass': 360,
        'Energy storage': 0,
        'Fossil Brown coal/Lignite': 363.6,
        'Fossil Coal-derived gas': 159.84,
        'Fossil Gas': 201.96,
        'Fossil Hard coal': 340.56,
        'Fossil Oil shale': 385.2,
        'Fossil Oil': 263.88,
        'Fossil Peat': 381.6,
        'Geothermal': 0,
        'Hydro Pumped Storage': 0,
        'Hydro Run-of-river and pondage': 0,
        'Hydro Water Reservoir': 0,
        'Marine': 0,
        'Nuclear': 0,
        'Other renewable': 0,
        'Other': 263.88,
        'Solar': 0,
        'Waste': 330.12,
        'Wind Offshore': 0,
        'Wind Onshore': 0,
    }
    
    # print("\n" + "="*70)
    # print("STEP 2: ALIGNING GENERATION DATES TO CONSUMPTION DATES")
    # print("="*70)
    
    # Parse consumption dates
    consumption[consumption_date_column] = pd.to_datetime(consumption[consumption_date_column])
    consumption_start = consumption[consumption_date_column].min()
    
    # print(f"Consumption starts at: {consumption_start}")
    # print(f"Original generation format: {generation[generation_date_column].iloc[0]}")
    
    # Extract start timestamp from generation intervals
    first_gen_interval = generation[generation_date_column].iloc[0]
    gen_start_str = first_gen_interval.split(' - ')[0]
    gen_start = pd.to_datetime(gen_start_str, format='%d/%m/%Y %H:%M:%S')
    
    # print(f"Original generation starts at: {gen_start}")
    
    # Calculate time difference
    time_diff = consumption_start - gen_start
    # print(f"Time shift needed: {time_diff}")
    
    # Shift all generation dates
    # print("Shifting generation timestamps...")
    new_generation_dates = []
    for interval in generation[generation_date_column]:
        parts = interval.split(' - ')
        start = pd.to_datetime(parts[0], format='%d/%m/%Y %H:%M:%S')
        end = pd.to_datetime(parts[1], format='%d/%m/%Y %H:%M:%S')
        
        # Shift both start and end
        new_start = start + time_diff
        new_end = end + time_diff
        
        # Format back to string
        new_interval = f"{new_start.strftime('%d/%m/%Y %H:%M:%S')} - {new_end.strftime('%d/%m/%Y %H:%M:%S')}"
        new_generation_dates.append(new_interval)
    
    generation[generation_date_column] = new_generation_dates
    # print(f"✓ Generation dates shifted")
    # print(f"New generation format: {generation[generation_date_column].iloc[0]}")
    
    # print("\n" + "="*70)
    # print("STEP 3: CALCULATING GRID CO2 INTENSITY")
    # print("="*70)
    
    # Convert generation to numeric
    generation['Generation (MW)'] = pd.to_numeric(generation['Generation (MW)'], errors='coerce')
    
    # Pivot generation data
    generation_pivot = generation.pivot_table(
        index=generation_date_column,
        columns='Production Type',
        values='Generation (MW)',
        aggfunc='sum'
    ).fillna(0)
    
    # print(f"✓ Generation data pivoted: {generation_pivot.shape}")
    
    time_hours = 0.25  # 15 minutes
    
    # Calculate CO2 per production type
    co2_by_type = pd.DataFrame(index=generation_pivot.index)
    for prod_type in generation_pivot.columns:
        factor = emission_mapping.get(prod_type, 0)
        co2_by_type[prod_type] = generation_pivot[prod_type] * time_hours * factor
    
    # Total CO2 and energy
    total_co2 = co2_by_type.sum(axis=1)
    total_energy = generation_pivot.sum(axis=1) * time_hours
    
    # CO2 intensity (kg/MWh)
    co2_intensity = total_co2 / total_energy.replace(0, np.nan)
    
    # print(f"✓ CO2 intensity calculated")
    # print(f"  Mean CO2 intensity: {co2_intensity.mean():.2f} kg/MWh")
    
    # print("\n" + "="*70)
    # print("STEP 4: MATCHING CONSUMPTION WITH CO2 INTENSITY")
    # print("="*70)
    
    # Prepare CO2 intensity dataframe
    co2_df = pd.DataFrame({'CO2_Intensity': co2_intensity})
    
    # Extract start timestamps from intervals for matching
    co2_df.index = pd.to_datetime(
        co2_df.index.str.split(' - ').str[0],
        format='%d/%m/%Y %H:%M:%S'
    )
    
    # Prepare consumption
    consumption.set_index(consumption_date_column, inplace=True)
    
    # Handle consumption/generation:
    # Negative values = consumption from grid (needs CO2 calculation)
    # Positive values = surplus generation (no CO2 emissions)
    raw_consumption = consumption[consumption_column]
    
    # Convert negative consumption to positive energy consumed
    consumption['Consumption_kW'] = raw_consumption * -1
    consumption['Energy_MWh'] = consumption['Consumption_kW'] * time_hours / 1000
    
    # Set energy to 0 when we have surplus (original positive values)
    # This means no grid consumption, so no CO2 emissions
    consumption.loc[raw_consumption > 0, 'Energy_MWh'] = 0
    consumption.loc[raw_consumption > 0, 'Consumption_kW'] = 0
    
    # Join dataframes
    result = consumption.join(co2_df, how='inner')
    
    # print(f"✓ Matched {len(result)} timesteps")
    
    if len(result) == 0:
        print("⚠ WARNING: No timestamps matched!")
        print(f"  Consumption range: {consumption.index.min()} to {consumption.index.max()}")
        print(f"  CO2 data range: {co2_df.index.min()} to {co2_df.index.max()}")
        return None
    
    # Calculate CO2 emissions
    result['CO2_emissions_kg'] = result['Energy_MWh'] * result['CO2_Intensity']
    
    # Calculate cumulative CO2 emissions
    result['Cumulative_CO2_kg'] = result['CO2_emissions_kg'].cumsum()
    result['Cumulative_CO2_tonnes'] = result['Cumulative_CO2_kg'] / 1000
    
    # print("\n" + "="*70)
    # print("STEP 5: SUMMARY STATISTICS")
    # print("="*70)
    
    total_energy = result['Energy_MWh'].sum()
    total_co2 = result['CO2_emissions_kg'].sum()
    cumulative_co2_final = result['Cumulative_CO2_kg'].iloc[-1]
    mean_co2 = result['CO2_emissions_kg'].mean()
    peak_co2 = result['CO2_emissions_kg'].max()
    
    #print(f"Total Energy Consumed:      {total_energy:.2f} MWh")
    print(f"Total CO2 Emissions:        {total_co2:,.2f} kg")
    print(f"                            {total_co2/1000:,.2f} tonnes")
    #print(f"Cumulative CO2 (final):     {cumulative_co2_final:,.2f} kg")
    #print(f"                            {cumulative_co2_final/1000:,.2f} tonnes")
    #print(f"Average CO2 per timestep:   {mean_co2:.2f} kg")
    #print(f"Peak CO2 in a timestep:     {peak_co2:.2f} kg")
    #print(f"Number of timesteps:        {len(result)}")
    #print("="*70)
    
    # Save results
    result.to_csv(output_csv)
    # print(f"\n✓ Results saved to: {output_csv}")
    
    return result


def plot_co2_emissions(result_df, title='CO2 Emissions Over Time', ax=None):
    
    """
    Plot CO2 emissions only.
    Supporting both standalone and side-by-side layouts.
    
    Parameters:
    -----------
    result_df : pd.DataFrame
        Results from align_dates_and_calculate_co2()
    title : str
        Plot title
    """
    if result_df is None or len(result_df) == 0:
        print("No data to plot!")
        return
 
    if result_df is None or len(result_df) == 0:
        print("No data to plot!")
        return
    
    # Handle whether to create a new figure or use an existing axis
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 5))
        is_standalone = True
    else:
        is_standalone = False
    
    # Plot emissions
    ax.plot(result_df.index, result_df['CO2_emissions_kg'], 
            linewidth=1.5, color='#d62728', label='CO2 Emissions')
    ax.fill_between(result_df.index, result_df['CO2_emissions_kg'], 
                     alpha=0.3, color='#d62728')
    
    # Add mean line
    mean_co2 = result_df['CO2_emissions_kg'].mean()
    ax.axhline(y=mean_co2, color='orange', linestyle='--', 
               linewidth=2, label=f'Mean: {mean_co2:.2f} kg', alpha=0.8)
    
    # Formatting (adjusted font sizes for better side-by-side fit)
    ax.set_xlabel('Time', fontsize=10, fontweight='bold')
    ax.set_ylabel('CO2 Emissions (kg)', fontsize=10, fontweight='bold')
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=9, framealpha=0.9)
    
    # Finalize only if not part of a larger subplot
    if is_standalone:
        plt.tight_layout()
        plt.show()


# ==============================================================================
# USAGE EXAMPLE - CHANGE THESE PATHS TO YOUR FILES
# ==============================================================================

if __name__ == "__main__":
    # File paths - UPDATE THESE
    generation_file = 'GENERATION_PER_TYPE_20251125-20251202.csv'
    consumption_file = 'your_consumption_file.csv'
    
    # Run the complete workflow
    results = align_dates_and_calculate_co2(
        generation_file=generation_file,
        consumption_file=consumption_file,
        consumption_column='Controller1.dump',  # Change if needed
        consumption_date_column='date',          # Change if needed
        output_csv='co2_emissions_results.csv'
    )
    
    # Plot results
    if results is not None:
        plot_co2_emissions(results, title='CO2 Emissions from Energy Consumption')