
import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display
import numpy as np

def run_energy_dashboard():
    """
    Run the interactive energy dashboard for the Energy HUB tutorial.
    Loads datasets, sets up widgets, and displays interactive plots.
    """
    # Load datasets
    df1 = pd.read_csv(r"data/load_data.txt", delimiter=",", header=1)
    df2 = pd.read_csv(r"data/nl_entsoe_demand_household.csv", delimiter=",", header=1)

    # Convert time columns to datetime
    df1['time'] = pd.to_datetime(df1['time'])
    df2['time'] = pd.to_datetime(df2['time'])

    # Set time as index
    df1_local = df1.set_index('time')
    df2_local = df2.set_index('time')

    # Scale both datasets for 100 houses
    df1_local['load'] = df1_local['load'] * 100
    df2_local['load'] = df2_local['Actual Total Load (MW)'] * 100

    # Select specific days for demonstration
    df1_day = df1_local[(df1_local.index.month == 2) & (df1_local.index.day == 1)]
    df2_day = df2_local[(df2_local.index.month == 11) & (df2_local.index.day == 28)]

    datasets = {
        "Rotterdam": df1_day,
        "Netherlands": df2_day,
    }


    # Constants
    p_rated_turbine = 100  # kW per wind turbine (small commercial turbine)
    pv_capacity_per_panel = 0.3  # kW per PV panel

    # Internal state variables
    current_df_day = None
    current_load = None
    current_t_hours = None
    current_pv_shape = None
    current_wind_shape = None
    storage_patch = None

    # Set up the figure
    fig, ax = plt.subplots(figsize=(10, 5))
    (line_load,) = ax.plot([], [], label="Load (100 houses)", linewidth=2)
    (line_pv,) = ax.plot([], [], "--", label="Solar", linewidth=1.5, color="orange")
    (line_wind,) = ax.plot([], [], "--", label="Wind", linewidth=1.5, color="grey")
    (line_total,) = ax.plot([], [], "--", label="Solar + Wind", linewidth=2, color="green")
    (line_store,) = ax.plot([], [], ":", label="Charge/Discharge", linewidth=2, color="purple")

    ax.legend()
    ax.grid(True)
    ax.set_ylabel("Power [kW]")
    plt.xticks(rotation=30)
    plt.tight_layout()


    # Widgets for user interaction
    dropdown = widgets.Dropdown(
        options=list(datasets.keys()),
        description="Dataset:",
    )
    pv_size_slider = widgets.IntSlider(
        value=150, min=0, max=300, step=10,
        description="PV panels installed"
    )
    n_t_slider = widgets.IntSlider(
        value=0, min=0, max=3, step=1,
        description="Wind Turbines"
    )
    storage_slider = widgets.IntSlider(
        value=200, min=0, max=1000, step=10,
        description="Storage Capacity (kWh)"
    )


    def update_dataset(dataset_name):
        """
        Update the data when the dataset selection changes.
        """
        nonlocal current_df_day, current_load, current_t_hours
        nonlocal current_pv_shape, current_wind_shape

        current_df_day = datasets[dataset_name]
        current_load = current_df_day["load"]
        current_t_hours = (
            (current_df_day.index - current_df_day.index[0]).total_seconds() / 3600.0
        )

        # Calculate PV and wind shapes for this dataset
        pv_raw = np.sin(np.pi * (current_t_hours - 6) / 12.0)
        pv_raw = np.clip(pv_raw, 0, None)
        current_pv_shape = pv_raw / pv_raw.max() if pv_raw.max() > 0 else pv_raw

        rng = np.random.default_rng(42)
        wind_speed = rng.normal(7.0, 1.8, len(current_t_hours))
        wind_speed = np.clip(wind_speed, 0, None)
        current_wind_shape = np.zeros_like(wind_speed)
        mask1 = (wind_speed >= 3) & (wind_speed < 12)
        mask2 = (wind_speed >= 12) & (wind_speed <= 25)
        current_wind_shape[mask1] = (wind_speed[mask1] / 12) ** 3
        current_wind_shape[mask2] = 1.0

        # Update load curve and plot limits
        line_load.set_data(current_df_day.index, current_load)
        ax.set_xlim(current_df_day.index.min(), current_df_day.index.max())
        ax.set_title(f"Energy Generation and Load - {dataset_name}")


    def update_sliders(*args):
        """
        Update the generation and storage curves when sliders change.
        """
        nonlocal storage_patch
        if current_df_day is None:
            return
        # Get slider values
        pv_number = pv_size_slider.value
        pv_size = pv_number * pv_capacity_per_panel
        n_turbines = n_t_slider.value
        storage_lvl = storage_slider.value

        # Calculate power (all in kW)
        pv_power = pv_size * current_pv_shape
        wind_power = n_turbines * p_rated_turbine * current_wind_shape
        total = pv_power + wind_power

        # Battery logic: calculate actual power flow in kW
        net_flow = total - current_load
        current_soc = 0  # State of charge (kWh)
        actual_battery_kw = []
        for flow in net_flow:
            if flow > 0:
                charge_power = min(flow, storage_lvl - current_soc)
                actual_battery_kw.append(charge_power)
                current_soc += charge_power
            else:
                discharge_power = max(flow, -current_soc)
                actual_battery_kw.append(discharge_power)
                current_soc += discharge_power
        

        storage_power = np.array(actual_battery_kw)

        # Update plot lines and area
        line_store.set_data(current_df_day.index, storage_power)
        if storage_patch is not None:
            storage_patch.remove()
        storage_patch = ax.fill_between(
            current_df_day.index, 0, storage_power,
            alpha=0.3, color="purple", label="Battery kW"
        )
        line_pv.set_data(current_df_day.index, pv_power)
        line_wind.set_data(current_df_day.index, wind_power)
        line_total.set_data(current_df_day.index, total)
        line_store.set_data(current_df_day.index, storage_power)

        # Adjust Y-limits
        s_min = np.min(storage_power) if len(storage_power) > 0 else 0
        s_max = np.max(storage_power) if len(storage_power) > 0 else 0
        ymin = min(0, s_min)
        ymax = max(current_load.max(), total.max(), s_max, 10)
        ax.set_ylim(ymin - 15, ymax * 1.2)
        fig.canvas.draw_idle()

    # Callbacks for widget changes
    def on_dropdown_change(change):
        if change["type"] == "change" and change["name"] == "value":
            update_dataset(change["new"])
            update_sliders()

    def on_slider_change(change):
        if change["type"] == "change" and change["name"] == "value":
            update_sliders()


    # Connect widget events
    dropdown.observe(on_dropdown_change, names="value")
    pv_size_slider.observe(on_slider_change, names="value")
    n_t_slider.observe(on_slider_change, names="value")
    storage_slider.observe(on_slider_change, names="value")

    # Display widgets
    display(
        widgets.VBox([
            dropdown,
            widgets.HTML("<hr>"),
            pv_size_slider,
            n_t_slider,
            storage_slider,
        ])
    )

    # Initialize dashboard
    update_dataset(dropdown.value)
    update_sliders()

    # Return objects for further use if needed
    return {
        "fig": fig,
        "ax": ax,
        "dropdown": dropdown,
        "pv_size_slider": pv_size_slider,
        "n_t_slider": n_t_slider,
        "storage_slider": storage_slider,
        "p_rated_turbine": p_rated_turbine,
        "datasets": datasets,
    }
