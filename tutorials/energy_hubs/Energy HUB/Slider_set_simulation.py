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

    CONFIG_FILE = 'data\Sliders_Scenario_grid.yaml'
    simulation_RES = Simulation(CONFIG_FILE)

    load_files = {
        "Rotterdam": "data\load_data.txt",
        "Netherlands": "nl_entsoe_demand_household_cleaned.csv",
    }

    pv_files = {
        "Rotterdam": "data\pv_data_Rotterdam_NL-15min.txt",
        "Netherlands": "pv_data_Rotterdam_NL-15min_2025.txt",
    }

    wind_files = {
        "Rotterdam": "data\winddata_NL.txt",
        "Netherlands": "winddata_NL_2025.txt",
    }

    times = {
        "Rotterdam": {
            'start_time': '2012-02-01 00:00:00',
            'end_time': '2012-02-01 23:45:00'
        },
        "Netherlands": {
            'start_time': '2025-11-28 00:00:00',
            'end_time': '2025-12-02 23:45:00'
        }
    }

    def int_to_vector(n, length=10):
        return [1]*n + [0]*(length-n)

    def apply_ui_to_simulation():
        selected_dataset = dropdown.value

        simulation_RES.set_model_param(
            model_name='CSVload',
            parameter='file_path',
            value=load_files[selected_dataset]
        )
        simulation_RES.set_model_param(
            model_name='CSV_pv',
            parameter='file_path',
            value=pv_files[selected_dataset]
        )
        simulation_RES.set_model_param(
            model_name='CSV_wind',
            parameter='file_path',
            value=wind_files[selected_dataset]
        )

        simulation_RES.set_scenario_param('start_time', times[selected_dataset]['start_time'])
        simulation_RES.set_scenario_param('end_time', times[selected_dataset]['end_time'])

        pv_number     = pv_size_slider.value
        pv_size_kW    = pv_number * 250      # kW
        n_turbines    = n_t_slider.value
        storage_level = storage_slider.value

        Turbines_on = int_to_vector(n_turbines)

        pv_cap_W = pv_size_kW * 1000

        new_settings = {
            'Wind1':  {'p_rated': Turbines_on[0]*p_rated_turbine},
            'Wind2':  {'p_rated': Turbines_on[1]*p_rated_turbine},
            'Wind3':  {'p_rated': Turbines_on[2]*p_rated_turbine},
            'Wind4':  {'p_rated': Turbines_on[3]*p_rated_turbine},
            'Wind5':  {'p_rated': Turbines_on[4]*p_rated_turbine},
            'Wind6':  {'p_rated': Turbines_on[5]*p_rated_turbine},
            'Wind7':  {'p_rated': Turbines_on[6]*p_rated_turbine},
            'Wind8':  {'p_rated': Turbines_on[7]*p_rated_turbine},
            'Wind9':  {'p_rated': Turbines_on[8]*p_rated_turbine},
            'Wind10': {'p_rated': Turbines_on[9]*p_rated_turbine},
            'PV1':     {'cap': pv_cap_W},
            'Battery1': {
                'max_p':      storage_level,
                'min_p':     -storage_level,
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
    simulation_RES.edit_models(new_settings)

    csvload_model = [m for m in simulation_RES.config['models'] if m['name'] == 'CSVload'][0]
    path = csvload_model['parameters']['file_path']
    print("CSVload file path:", repr(path))
    print("Exists on disk? ->", os.path.exists(path))

    df_load = pd.read_csv(path, delimiter=",", nrows=5)
    print("Columns as seen by pandas:")
    for c in df_load.columns:
        print("  ", repr(c))

    simulation_RES.run()

    return simulation_RES, new_settings, df_load
