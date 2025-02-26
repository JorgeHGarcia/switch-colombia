import pandas as pd

def get_xm_reports():
    """
    Retrieve and preprocess hydro generation data from XM reports.

    Returns:
        pd.DataFrame: Preprocessed hydro generation data containing columns
                      ['Values_Name', 'Value', 'Datetime'].
    """
    dema_path = '../../data/XM-API/variable_query/'

    # Load resource metadata
    resources = pd.read_csv(dema_path + '2022-12-01_2023-11-30/LitadoRecursos_Sistema.csv')
    resources = resources.drop(resources.columns[0], axis=1)
    # Only water sources
    resources = resources[resources['Values_EnerSource'] == 'AGUA']

    # Load generation data for 2023, 2022, and 2021
    generation_files = [
        dema_path + '2022-12-01_2023-11-30/Gene_Recurso.csv',
        dema_path + '2021-12-01_2022-11-30/Gene_Recurso.csv',
        dema_path + '2020-12-01_2021-11-30/Gene_Recurso.csv'
    ]

    generation = pd.concat([
        pd.read_csv(file).drop(columns=[pd.read_csv(file).columns[0]]) for file in generation_files
    ], axis=0)

    # Melt the dataframe to long format
    id_vars = ['Id', 'Values_code', 'Date']
    value_vars = [col for col in generation.columns if col.startswith('Values_Hour')]
    generation = pd.melt(
        generation, id_vars=id_vars, value_vars=value_vars,
        var_name='Hour', value_name='Value'
    )

    # Process and combine the 'Date' and 'Hour' columns into a datetime index
    generation['Hour'] = generation['Hour'].str.replace('Values_Hour', '', regex=True).astype(int)
    generation['Datetime'] = pd.to_datetime(generation['Date']) + pd.to_timedelta(generation['Hour'] - 1, unit='h')

    # Drop unnecessary columns and convert 'Value' to MW
    generation.drop(['Id', 'Date', 'Hour'], axis=1, inplace=True)
    generation['Value'] = generation['Value'] / 1000

    # Filter hydro generation by merging with resources metadata
    generation = pd.merge(
        generation, resources,
        left_on="Values_code", right_on="Values_Code", how="inner"
    )
    generation = generation[['Values_Name', 'Value', 'Datetime']]

    return generation

def to_swcol_names(model_path, generation, base_year):
    """
    Map XM hydro generation data to SWCOL-compatible naming conventions.

    Args:
        generation (pd.DataFrame): Hydro generation data containing ['Values_Name', 'Value', 'Datetime'].
        base_year (int): Base year to filter active hydro projects.

    Returns:
        pd.DataFrame: Mapped hydro generation data with SWCOL-compatible names.
    """
    gen_build_predetermined = pd.read_csv(model_path + 'gen_build_predetermined.csv')
    gen_info = pd.read_csv(model_path + 'gen_info.csv')

    # Filter hydro projects active before the base year
    hydro_active = pd.merge(gen_build_predetermined, gen_info, on="GENERATION_PROJECT", how="inner")
    hydro_active = hydro_active[(hydro_active['gen_tech'] == 'Hidro') & (hydro_active['build_year'] <= base_year)]
    hydro_active = hydro_active[['GENERATION_PROJECT', 'build_gen_predetermined']]

    # Load mapping between XM and SWCOL names
    map_xm = pd.read_csv('../../data/XM-API/Map.csv').dropna()
    map_xm = pd.merge(map_xm, hydro_active, on='GENERATION_PROJECT', how='inner')
    map_xm = map_xm[['GENERATION_PROJECT', 'Values_Name']]
    map_xm.rename(columns={'GENERATION_PROJECT': 'Name', 'Values_Name': 'Best Match'}, inplace=True)

    # Map XM generation data to SWCOL names
    generation = pd.merge(generation, map_xm, left_on="Values_Name", right_on="Best Match", how="inner")
    generation['Datetime'] = pd.to_datetime(generation['Datetime'])

    return generation

import swcol as sc
def cluster(generation, base_year, percentile):
    """
    Cluster hydro generation data by timestamp and calculate statistics.

    Args:
        generation (pd.DataFrame): Mapped hydro generation data.
        base_year (int): Base year for clustering.
        percentile (float): Percentile for calculating flow statistics.

    Returns:
        pd.DataFrame: Clustered hydro generation data with flow statistics.
    """
    generation = generation.copy()

    # Create timestamp based on quarters and days of the week
    generation['timestamp'] = generation['Datetime'].apply(
        lambda x: f"{base_year}_{sc.rain_seasons.quarter(x.strftime('%B'))}_{sc.rain_seasons.day(x.day_name())}"
    )
    generation = generation[['Name', 'Value', 'timestamp']]

    # Group and calculate statistics
    fname = f"f{percentile}"
    generation['min'] = generation['Value']
    generation[fname] = generation['Value']

    generation = generation.groupby(['Name', 'timestamp']).agg({
        fname: lambda x: x.quantile(percentile),
        'min': 'min'
    }).reset_index()

    # Create missing combinations and fill with zeros
    timestamp = pd.DataFrame({'timestamp': [
        f"{base_year}_Q1_labor", f"{base_year}_Q1_holidays",
        f"{base_year}_Q2_labor", f"{base_year}_Q2_holidays",
        f"{base_year}_Q3_labor", f"{base_year}_Q3_holidays",
        f"{base_year}_Q4_labor", f"{base_year}_Q4_holidays"
    ]})
    combination = pd.DataFrame(
        [(name, date) for name in generation['Name'].unique() for date in timestamp['timestamp']],
        columns=['Name', 'timestamp']
    )
    missing_generation = combination[~combination.set_index(['Name', 'timestamp']).index.isin(
        generation.set_index(['Name', 'timestamp']).index
    )].copy()
    missing_generation['min'] = 0
    missing_generation[fname] = 0

    # Combine and rename columns
    generation = pd.concat([generation, missing_generation], axis=0).reset_index(drop=True)
    generation.rename(columns={
        'Name': 'hydro_project',
        'timestamp': 'timeseries',
        'min': 'hydro_min_flow_mw',
        fname: 'hydro_avg_flow_mw'
    }, inplace=True)

    return generation

def generate(model_path, generation, period, cycles, base_year):
    """
    Generate future hydro timeseries based on historical data.

    Args:
        model_path (str): Path to save the generated timeseries.
        generation (pd.DataFrame): Clustered hydro generation data.
        period (int): Time interval between cycles in years.
        cycles (int): Number of future cycles to generate.
        base_year (int): Starting year for the timeseries.

    Returns:
        pd.DataFrame: Generated hydro timeseries.
    """
    year = base_year
    hydro_timeseries = pd.DataFrame()

    # Generate timeseries for each cycle
    for _ in range(cycles):
        hydro_future = generation.copy()
        hydro_future['timeseries'] = hydro_future['timeseries'].str.replace(str(base_year), str(year))
        hydro_timeseries = pd.concat([hydro_timeseries, hydro_future], axis=0)
        year += period

    # Save the generated timeseries to a CSV file
    hydro_timeseries.reset_index(drop=True, inplace=True)
    hydro_timeseries.to_csv(model_path + 'hydro_timeseries.csv', index=False)
    print('Hydro Timeseries saved in ../../model/inputs/hydro_timeseries.csv')

    return hydro_timeseries
