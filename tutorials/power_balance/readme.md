
![Alt Text](images/banner1.png)

## Input Overview

### Wind, PV and Load Model

**Scenario Data**
- load_data.txt
- number of houses = 5 (load input data)
- winddata_NL.txt
- pv_data_Rotterdam_NL-15min.txt

**PV Inputs**

| **Input** | **Value** |
|----------|----------|
| Module Area           | 1.26 m^2  |
| NOCT                  | 44 °C     |
| Module Efficiency     | 0.198     |
| Irradiance at NOCT    | 800 W/m^2 |
| Power Output at STC   | 250 W     |
| Peak Power            | 600 W     |
| Module Tilt           | 14°       |
| Module Azimuth        | 180°      |
| Installed Capacity    | 500 W (= 0.5 kW)|

**Wind Inputs**

| **Input** | **Value** |
|----------|----------|
| Rated Power                   | 0.3 kW    |
| Rated Wind Speed (u_rated)    | 10.3 m/s  |
| Cut In Wind Speed (u_cutin)   | 2.8 m/s   |
| Cut Out Wind Speed            | 25 m/s    |
| Cp (Coefficient of Power)     | 0.4       |
| Diameter                      | 2         |
| (output type)                 | (power)   |

### Wind, PV, Load and Battery

Logic Controller: if more power generated than consumed by neighbourhood -> charge battery (left over power gets dumped in grid), if less power generated than consumed by neighbourhood -> discharge battery (until minimum SOC then take power from grid)

Time Shifted Connection between Battery and battery controller: SOC from previous time step

Sequence Simulators at each step : Load -> PV -> Wind -> Controller -> Battery 

Note: Load, PV and Wind are independent from each other so here sequence flexible (but important all three execute before controller)

PV & Wind Inputs are the same as in first case

**Battery Inputs**

| **Input** | **Value** |
|----------|----------|
| Initial SOC (defined at time shifted connection) | 80%  |
| Charge Efficiency         | 0.9 |
| Discharge Efficiency      | 0.9 |
| Max Power                 | 0.8 kW |
| Min Power                 | -0.8 kW |
| SOC Max                   | 90 |
| SOC Min                   | 10 |
| Max Energy                | 0.8 |



