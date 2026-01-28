import pandas as pd
import matplotlib.pyplot as plt

def plot_simulation_results(
    filepath="./out_Tutorial_5_Green.csv",
    variables=None,
    title="Simulation Results",
    figsize=(10,5)
):
    """
    Plot selected variables from Illuminator output CSV.
    
    Parameters
    ----------
    filepath : str
        Path to the output CSV defined in YAML (monitor.file).
    variables : list of str
        List of columns to plot. If None, will show all available numeric columns.
    title : str
        Title of the plot.
    figsize : tuple
        Figure size.
    """

    # Load the data
    df = pd.read_csv(filepath)

    # Detect time column
    time_col = df.columns[0]
    df[time_col] = pd.to_datetime(df[time_col])

    # Autodetect variables if none specified
    if variables is None:
        variables = [c for c in df.columns if c != time_col]

    # Plot
    plt.figure(figsize=figsize)

    for var in variables:
        if var not in df.columns:
            print(f"⚠ Skipping '{var}' (not in dataset)")
            continue
        plt.plot(df[time_col], df[var], label=var)

    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
