from illuminator.engine import Simulation
import pandas as pd
import nest_asyncio
import os

nest_asyncio.apply()

def run_res_simulation(dashboard):
    # prendo gli oggetti dai risultati della dashboard
    dropdown        = dashboard["dropdown"]
    pv_size_slider  = dashboard["pv_size_slider"]
    n_t_slider      = dashboard["n_t_slider"]
    storage_slider  = dashboard["storage_slider"]
    p_rated_turbine = dashboard["p_rated_turbine"]

    CONFIG_FILE = 'data\Tutorial_5.yaml'
    simulation_RES = Simulation(CONFIG_FILE)

    # def int_to_vector(n, length=10):
    #     return [1]*n + [0]*(length-n)

    def apply_ui_to_simulation():
        selected_dataset = dropdown.value
        pv_number     = pv_size_slider.value
        pv_size_kW    = pv_number * 300  # W
        n_turbines    = n_t_slider.value * 100 # kW (small commercial wind turbine)
        storage_level = storage_slider.value

        # Turbines_on = n_turbines

        new_settings = {

            'Wind1':  {'p_rated': n_turbines},
            'PV1':     {'cap': pv_size_kW},
            'Battery1': {
                'max_p':      storage_level*0.1,
                'min_p':      storage_level* -0.1,
                'max_energy': storage_level
            },
            'Controller1': {
                'battery_active': True,
                'max_p':          storage_level
            },
            'Load1': {
                'houses':      100,
                'output_type': 'power'
            },
        }

        print("\nSimulation updated:")
        print("  Dataset:", selected_dataset)
        print("  PV size:", pv_size_kW, "kW")
        print("  Turbines:", n_turbines)
        print("  Storage:", storage_level, "kW")

        return new_settings

    new_settings = apply_ui_to_simulation()
    # simulation_RES.edit_models(new_settings)

    csvload_model = [m for m in simulation_RES.config['models'] if m['name'] == 'CSVload'][0]
    path = csvload_model['parameters']['file_path']
    print("CSVload file path:", repr(path))
    print("Exists on disk? ->", os.path.exists(path))

    df_load = pd.read_csv(path, delimiter=",", nrows=5)
    print("Columns as seen by pandas:")
    for c in df_load.columns:
        print("  ", repr(c))

    # simulation_RES.run()

    return simulation_RES, new_settings, df_load
