import pandas as pd

def generate(model_path, cycles, period, base_year):
    """
    Generate timepoints, timeseries, and periods for energy modeling and save them as CSV files.

    Args:
        model_path (str): Path where the generated CSV files will be saved.
        cycles (int): Number of cycles for data generation.
        period (int): Duration of each cycle in years.
        base_year (int): Starting year for the timepoint data.

    Returns:
        pd.DataFrame: DataFrame containing timepoints data.
    """
    # Predefined constants for generation
    Quartiles = [1, 2, 3, 4]
    day_types = ["labor", "holidays"]
    hours = 24

    # Initialize lists to store generated data
    timepoints = []
    timeseries = []
    periods = []

    n = 0  # Timepoint ID counter

    # Generate data for each cycle
    for i in range(cycles):
        year = base_year + i * period
        periods.append([year, year, year + period - 1])

        for Q in Quartiles:
            Q_year = year
            for day_type in day_types:
                timeseries_name = f"{Q_year}_Q{Q}_{day_type}"

                if day_type == 'labor':
                    ts_scale = (365 / 4 / 7) * 6 * period
                else:
                    ts_scale = (365 / 4 / 7) * period

                timeseries.append([timeseries_name, Q_year, 1, 24, ts_scale])

                for hour in range(hours):
                    n += 1
                    timepoint_id = str(n)
                    timestamp = f"{Q_year}_Q{Q}_{day_type}_{hour}h"
                    timepoints.append([timepoint_id, timestamp, timeseries_name])

    # Convert lists to DataFrames
    timepoints_df = pd.DataFrame(timepoints, columns=["timepoint_id", "timestamp", "timeseries"])
    timeseries_df = pd.DataFrame(timeseries, columns=["TIMESERIES", "ts_period", "ts_duration_of_tp", "ts_num_tps", "ts_scale_to_period"])
    periods_df = pd.DataFrame(periods, columns=["INVESTMENT_PERIOD", "period_start", "period_end"])

    # Save DataFrames to CSV
    timepoints_df.to_csv(model_path + 'timepoints.csv', index=False)
    print(f"File written: {model_path}timepoints.csv")

    timeseries_df.to_csv(model_path + 'timeseries.csv', index=False)
    print(f"File written: {model_path}timeseries.csv")

    periods_df.to_csv(model_path + 'periods.csv', index=False)
    print(f"File written: {model_path}periods.csv")

    return timepoints_df


def save_loads(model_path, loads, timepoints):
    """
    Merge load data with timepoints, reformat, and save to a CSV file.

    Args:
        model_path (str): Path where the loads CSV file will be saved.
        loads (pd.DataFrame): DataFrame containing load data with a 'timestamp' column.
        timepoints (pd.DataFrame): DataFrame containing timepoints data.

    Returns:
        pd.DataFrame: Processed DataFrame containing the merged load data.
    """
    # Merge loads with timepoints
    loads = pd.merge(loads, timepoints, on='timestamp', how='inner')
    loads['timepoint_id'] = pd.to_numeric(loads['timepoint_id'], errors='coerce')

    # Reorder and rename columns
    loads = loads[['Zone', 'timepoint_id', 'demand_mw']].sort_values(by='timepoint_id', ascending=False)
    loads.columns = ['LOAD_ZONE', 'timepoints', 'zone_demand_mw']

    # Save loads to CSV
    loads.to_csv(model_path + 'loads.csv', index=False)
    print(f"File written: {model_path}loads.csv")

    return loads
