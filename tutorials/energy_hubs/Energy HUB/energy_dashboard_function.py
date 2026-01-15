import pandas as pd
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display
import numpy as np

def run_energy_dashboard():
    # ========== CARICAMENTO DATASETS ==========
    df1 = pd.read_csv(
        r"data\load_data.txt",
        delimiter=",",
        header=1
    )

    df2 = pd.read_csv(
        r"data\nl_entsoe_demand_household.csv",
        delimiter=",",
        header=1
    )

    # Pulizia dati df2
    df2['time'] = pd.to_datetime(df2['time'])

    # Preparazione dataframes
    df1['time'] = pd.to_datetime(df1['time'])
    df1_local = df1.set_index('time')
    df2_local = df2.set_index('time')

    # Scala entrambi i dataset per 100 case
    df1_local['load'] = df1_local['load'] * 100  # kW → kW per 100 case
    df2_local['load'] = df2_local['Actual Total Load (MW)'] * 100  # kW → kW per 100 case

    # Selezione giorni specifici
    df1_day = df1_local[(df1_local.index.month == 2) & (df1_local.index.day == 1)]
    df2_day = df2_local[(df2_local.index.month == 11) & (df2_local.index.day == 28)]

    datasets = {
        "Rotterdam": df1_day,
        "Netherlands": df2_day,
    }

    # ========== COSTANTI ==========
    p_rated_turbine = 10.0  # kW per turbine

    # ========== VARIABILI "GLOBALI" (ma chiuse nella funzione) ==========
    current_df_day = None
    current_load = None
    current_t_hours = None
    current_pv_shape = None
    current_wind_shape = None
    storage_patch = None

    # ========== SETUP FIGURA ==========
    fig, ax = plt.subplots(figsize=(10, 5))
    (line_load,) = ax.plot([], [], label="Load (100 houses)", linewidth=2)
    (line_pv,) = ax.plot([], [], "--", label="PV", linewidth=1.5)
    (line_wind,) = ax.plot([], [], "--", label="Wind", linewidth=1.5)
    (line_total,) = ax.plot([], [], label="PV + Wind", linewidth=2, color="red")
    (line_store,) = ax.plot([], [], ":", label="Storage level", linewidth=2)

    ax.legend()
    ax.grid(True)
    ax.set_ylabel("Power [kW]")
    plt.xticks(rotation=30)
    plt.tight_layout()

    # ========== WIDGETS ==========
    dropdown = widgets.Dropdown(
        options=list(datasets.keys()),
        description="Dataset:",
    )

    pv_size_slider = widgets.IntSlider(
        value=20, min=0, max=80, step=1,
        description="PV's installed (integer)"
    )

    n_t_slider = widgets.IntSlider(
        value=2, min=0, max=50, step=1,
        description="Turbines (integer)"
    )

    storage_slider = widgets.FloatSlider(
        value=0, min=0, max=1000, step=10,
        description="Storage (kW)"
    )

    # ========== FUNZIONE PER CAMBIARE DATASET ==========
    def update_dataset(dataset_name):
        """Aggiorna i dati base quando cambia il dataset"""
        nonlocal current_df_day, current_load, current_t_hours
        nonlocal current_pv_shape, current_wind_shape

        current_df_day = datasets[dataset_name]
        current_load = current_df_day["load"]  # Già in kW, nessuna conversione
        current_t_hours = (
            (current_df_day.index - current_df_day.index[0]).total_seconds() / 3600.0
        )

        # Calcola forme PV e Wind per questo dataset
        pv_raw = np.sin(np.pi * (current_t_hours - 6) / 12.0)
        pv_raw = np.clip(pv_raw, 0, None)
        current_pv_shape = pv_raw / pv_raw.max() if pv_raw.max() > 0 else pv_raw

        wind_raw = 0.6 + 0.3 * np.sin(2 * np.pi * (current_t_hours - 4) / 24.0)
        current_wind_shape = wind_raw / wind_raw.max() if wind_raw.max() > 0 else wind_raw

        # Aggiorna curva load
        line_load.set_data(current_df_day.index, current_load)

        # Aggiorna limiti X
        ax.set_xlim(current_df_day.index.min(), current_df_day.index.max())

        # Aggiorna titolo
        ax.set_title(f"Energy Generation and Load - {dataset_name}")

    # ========== FUNZIONE PER AGGIORNARE SOLO GLI SLIDER ==========
    def update_sliders(*args):
        """Aggiorna solo le curve di generazione (veloce)"""
        nonlocal storage_patch

        if current_df_day is None:
            return

        # Valori slider
        pv_number = pv_size_slider.value
        pv_size = pv_number * 250  # W
        n_turbines = n_t_slider.value
        storage_lvl = storage_slider.value

        # Calcola potenze (tutto in kW)
        pv_power = pv_size * current_pv_shape
        wind_power = n_turbines * p_rated_turbine * current_wind_shape
        total = pv_power + wind_power
        storage_power = np.full_like(current_t_hours, storage_lvl, dtype=float)

        # Aggiorna linee
        line_pv.set_data(current_df_day.index, pv_power)
        line_wind.set_data(current_df_day.index, wind_power)
        line_total.set_data(current_df_day.index, total)
        line_store.set_data(current_df_day.index, storage_power)

        # Aggiorna area storage
        if storage_patch is not None:
            storage_patch.remove()
        storage_patch = ax.fill_between(
            current_df_day.index,
            storage_power,
            total,
            alpha=0.2,
            color="blue",
        )

        # Aggiorna limiti Y
        ymax = max(current_load.max(), total.max(), storage_power.max(), 1)
        ax.set_ylim(0, ymax * 1.1)

        fig.canvas.draw_idle()

    # ========== CALLBACKS ==========
    def on_dropdown_change(change):
        """Quando cambia il dataset"""
        if change["type"] == "change" and change["name"] == "value":
            update_dataset(change["new"])
            update_sliders()

    def on_slider_change(change):
        """Quando cambiano gli slider"""
        if change["type"] == "change" and change["name"] == "value":
            update_sliders()

    # ========== CONNESSIONE EVENTI ==========
    dropdown.observe(on_dropdown_change, names="value")
    pv_size_slider.observe(on_slider_change, names="value")
    n_t_slider.observe(on_slider_change, names="value")
    storage_slider.observe(on_slider_change, names="value")

    # ========== DISPLAY WIDGETS ==========
    display(
        widgets.VBox(
            [
                dropdown,
                widgets.HTML("<hr>"),
                pv_size_slider,
                n_t_slider,
                storage_slider,
            ]
        )
    )

    # ========== INIZIALIZZAZIONE ==========
    update_dataset(dropdown.value)
    update_sliders()

    # ========== RETURN OGGETTI PER ALTRE FUNZIONI ==========
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
