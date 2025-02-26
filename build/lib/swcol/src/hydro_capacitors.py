import pandas as pd
import swcol as sc

def get_xm_reports():
    """
    Load XM reports, filter for hydroelectric resources, and preprocess generation data.
    Returns a dataframe with generation data for hydroelectric resources.
    """
    dema_path = '../../data/XM-API/variable_query/'

    # Load resource metadata
    resources = pd.read_csv(dema_path + '2022-12-01_2023-11-30/LitadoRecursos_Sistema.csv')
    resources = resources.drop(resources.columns[0], axis=1)
    resources = resources[resources['Values_EnerSource'] == 'AGUA']

    # Load generation data for multiple years
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

    # Combine 'Date' and 'Hour' into a datetime index
    generation['Hour'] = generation['Hour'].str.replace('Values_Hour', '', regex=True).astype(int)
    generation['Datetime'] = pd.to_datetime(generation['Date']) + pd.to_timedelta(generation['Hour'] - 1, unit='h')

    # Drop unnecessary columns and convert 'Value' to MW
    generation.drop(['Id', 'Date', 'Hour'], axis=1, inplace=True)
    generation['Value'] = generation['Value'] / 1000

    # Merge with resources to filter hydroelectric generation
    generation = pd.merge(
        generation, resources,
        left_on="Values_code", right_on="Values_Code", how="inner"
    )

    return generation[['Values_Name', 'Value', 'Datetime']]

def to_swcol_names(model_path, generation):
    """
    Map XM generation data to SWCOL names.
    Returns a dataframe with SWCOL-compatible names.
    """
    gen_build_predetermined = pd.read_csv(model_path + 'gen_build_predetermined.csv')
    gen_info = pd.read_csv(model_path + 'gen_info.csv')
    gen_info = gen_info[gen_info['gen_energy_source'] == 'RunofRiver']

    # Filter hydro projects active before the base year
    hydro_active = pd.merge(gen_build_predetermined, gen_info, on="GENERATION_PROJECT", how="inner")
    hydro_active = hydro_active[['GENERATION_PROJECT', 'build_gen_predetermined']]

    # Load mapping between XM and SWCOL names
    map_xm = pd.read_csv('../../data/XM-API/Map.csv').dropna()
    map_xm = pd.merge(map_xm, hydro_active, on='GENERATION_PROJECT', how='inner')
    map_xm = map_xm[['GENERATION_PROJECT', 'Values_Name']]
    map_xm.rename(columns={'GENERATION_PROJECT': 'Name', 'Values_Name': 'Best Match'}, inplace=True)

    # Map XM generation data to SWCOL names
    generation = pd.merge(generation, map_xm, left_on="Values_Name", right_on="Best Match", how="inner")
    generation['Datetime'] = pd.to_datetime(generation['Datetime'])

    return generation[['Name', 'Value', 'Datetime']]

def cluster(generation, base_year):
    """
    Cluster generation data by timestamp and calculate mean values.
    Returns a clustered dataframe.
    """
    generation = generation.copy()
    generation['Datetime'] = pd.to_datetime(generation['Datetime'])
    generation['timestamp'] = generation['Datetime'].apply(
        lambda x: f"{base_year}_{sc.rain_seasons.quarter(x.strftime('%B'))}_{sc.rain_seasons.day(x.day_name())}_{x.hour}h"
    )

    generation = generation.groupby(['Name', 'timestamp']).agg({
        'Value': 'mean'
    }).reset_index()

    return generation

def normalize(model_path, generation):
    """
    Normalize generation values based on predetermined build capacity and clip at 1.
    Returns a normalized dataframe.
    """
    gen_build_predetermined = pd.read_csv(model_path + 'gen_build_predetermined.csv')
    timepoints = pd.read_csv(model_path + 'timepoints.csv')

    generation = pd.merge(generation, gen_build_predetermined,
                          left_on='Name', right_on="GENERATION_PROJECT", how="inner")

    generation['Value'] = generation['Value'] / generation['build_gen_predetermined']
    generation['Value'] = generation['Value'].clip(upper=1)

    generation = pd.merge(
        generation, timepoints,
        on='timestamp', how="inner")

    generation = generation[['Name', 'timepoint_id', 'Value']]
    generation.rename(columns={
        'Name': 'GENERATION_PROJECT',
        'Value': 'gen_max_capacity_factor'
    }, inplace=True)

    return generation

def generate(model_path, generation, period, cycles):
    """
    Generate and concatenate future timepoints for hydro variable capacitors.
    Returns the final concatenated dataframe.
    """
    minors_total = pd.DataFrame()
    n_timepoints = 0
    for i in range(cycles):
        minors_future = generation.copy()
        minors_future['timepoint_id'] = minors_future['timepoint_id'] + (192 * n_timepoints)
        minors_total = pd.concat([minors_total, minors_future], axis=0)
        n_timepoints += period

    minors_total.reset_index(drop=True, inplace=True)

    # Concatenate with existing variable capacitors
    variable_capacity_factors = pd.read_csv(model_path + 'variable_capacity_factors.csv')
    generation = pd.concat([variable_capacity_factors, minors_total], axis=0)
    generation.to_csv(model_path + 'variable_capacity_factors.csv', index=False)

    print('Hydro Variable Capacitors concatenated with ../../model/inputs/variable_capacity_factors.csv')
    return generation
