import pandas as pd

# Function to load and process variable capacity data from a given reference path
def get_reference(reference_path):
    """
    Load and process variable capacity data.

    Args:
        reference_path (str): Path to the reference model directory.

    Returns:
        pd.DataFrame: Processed variable capacity data with columns 'GENERATION_PROJECT', 'gen_max_capacity_factor', and 'Date'.
    """
    variable_capacity = pd.read_csv(reference_path + 'variable_capacity_factors.csv')
    timepoints = pd.read_csv(reference_path + 'timepoints.csv')

    # Merge variable capacity data with timepoints to include timestamps
    variable_capacity = pd.merge(variable_capacity, timepoints, 
                                 left_on="timepoint", right_on="timepoint_id", how="left")

    # Convert timestamps into dates
    variable_capacity['Date'] = pd.to_datetime(variable_capacity['timestamp'])

    # Select relevant columns
    variable_capacity = variable_capacity[['GENERATION_PROJECT', 'gen_max_capacity_factor', 'Date']]

    return variable_capacity

# Function to group variable capacity data by timestamp and format it for analysis
def cluster(variable_capacity, base_year):
    """
    Group and cluster variable capacity data by timestamp.

    Args:
        variable_capacity (pd.DataFrame): Variable capacity data with a 'Date' column.
        base_year (int): The base year for formatting the data.

    Returns:
        pd.DataFrame: Clustered variable capacity data.
    """
    variable_capacity = swcol.rain_seasons.format_year(variable_capacity, base_year)

    # Group by generation project and timestamp, calculating the mean capacity factor
    variable_capacity = variable_capacity.groupby(['GENERATION_PROJECT', 'timestamp']).agg({
        'gen_max_capacity_factor': 'mean'
    }).reset_index()

    return variable_capacity

# Function to merge clustered variable capacity with timepoints
def merge_timepoints(variable_capacity, timepoints):
    """
    Merge variable capacity data with timepoints to map timepoint IDs.

    Args:
        variable_capacity (pd.DataFrame): Clustered variable capacity data.
        timepoints (pd.DataFrame): Timepoints data with 'timestamp' and 'timepoint_id'.

    Returns:
        pd.DataFrame: Variable capacity data with mapped timepoint IDs.
    """
    variable_capacity = pd.merge(variable_capacity, timepoints, on='timestamp', how='inner')

    # Sort and select relevant columns
    variable_capacity = variable_capacity.sort_values(by=['GENERATION_PROJECT', 'timepoint_id']).reset_index(drop=True)
    variable_capacity = variable_capacity[['GENERATION_PROJECT', 'timepoint_id', 'gen_max_capacity_factor']]

    # Save the result to a CSV file
    variable_capacity.to_csv('../../data/Colombia/exists_varcap.csv', index=False)
    print('Reference saved in ../../data/Colombia/exists_varcap.csv')

    return variable_capacity

# Function to generate a keymap for variable capacity data
def generate_keymap(variable_capacity, model_path):
    """
    Generate a keymap for variable capacity factors by grouping by technology and load zone.

    Args:
        variable_capacity (pd.DataFrame): Clustered variable capacity data.
        model_path (str): Path to the model directory containing generator information.

    Returns:
        pd.DataFrame: Keymap for variable capacity factors.
    """
    gen_info = pd.read_csv(model_path + 'gen_info.csv')

    # Merge variable capacity data with generator information
    keymap_varcap = pd.merge(variable_capacity, gen_info, on='GENERATION_PROJECT', how='inner')

    # Group by timepoint, technology, and load zone, and calculate the mean capacity factor
    keymap_varcap = keymap_varcap.groupby(['timepoint_id', 'gen_tech', 'gen_load_zone']).agg({
        'gen_max_capacity_factor': 'mean',
    }).reset_index()

    # Create a unique variable capacity ID for each tech-zone combination
    keymap_varcap['var_cap_id'] = keymap_varcap['gen_tech'] + keymap_varcap['gen_load_zone']

    # Sort and select relevant columns
    keymap_varcap = keymap_varcap.sort_values(by=['var_cap_id', 'timepoint_id']).reset_index(drop=True)
    keymap_varcap = keymap_varcap[['var_cap_id', 'timepoint_id', 'gen_max_capacity_factor']]

    # Save the keymap to a CSV file
    keymap_varcap.to_csv('../../data/Colombia/keymap_varcap.csv', index=False)
    print('Keymap saved in ../../data/Colombia/keymap_varcap.csv')

    return keymap_varcap

# Function to generate base year variable capacity data
def generate_base_year(model_path, generate_varcaps, base_year, timepoints):
    """
    Generate base year variable capacity data.

    Args:
        model_path (str): Path to the model directory.
        generate_varcaps (bool): Whether to generate variable capacity factors.
        base_year (int): Base year for formatting the data.
        timepoints (pd.DataFrame): Timepoints data.

    Returns:
        pd.DataFrame: Base year variable capacity data.
    """
    gen_info = pd.read_csv(model_path + 'gen_info.csv').drop_duplicates()

    # Filter variable generation projects (Solar and Wind)
    gen_info = gen_info[(gen_info['gen_is_variable'] == 1) & 
                        (gen_info['gen_energy_source'].isin(['Solar', 'Wind']))]

    if generate_varcaps:
        variable_capacity = swcol.variable_capacitors.get_reference('../../data/Reference/')
        variable_capacity = swcol.variable_capacitors.cluster(variable_capacity, base_year)
        exists_varcap = swcol.variable_capacitors.merge_timepoints(variable_capacity, timepoints)
        keymap_varcap = swcol.variable_capacitors.generate_keymap(exists_varcap, model_path)
    else:
        exists_varcap = pd.read_csv('../../data/Colombia/exists_varcap.csv')
        keymap_varcap = pd.read_csv('../../data/Colombia/keymap_varcap.csv')

    # Merge existing variable capacity with generator info
    var_cap_gen = pd.merge(exists_varcap, gen_info, on='GENERATION_PROJECT', how='inner')[
        ['GENERATION_PROJECT', 'timepoint_id', 'gen_max_capacity_factor']]

    # Identify projects without variable capacity data
    has_var_cap = set(var_cap_gen['GENERATION_PROJECT'])
    missing_var_cap = gen_info[~gen_info['GENERATION_PROJECT'].isin(has_var_cap)][
        ['GENERATION_PROJECT', 'gen_tech', 'gen_load_zone']]

    # Create variable capacity IDs for missing projects
    missing_var_cap['var_cap_id'] = missing_var_cap['gen_tech'] + missing_var_cap['gen_load_zone']
    missing_var_cap = missing_var_cap[['GENERATION_PROJECT', 'var_cap_id']]

    # Merge missing projects with keymap variable capacity
    keymap_varcap = pd.merge(keymap_varcap, missing_var_cap, on='var_cap_id', how='inner')[
        ['GENERATION_PROJECT', 'timepoint_id', 'gen_max_capacity_factor']]

    # Concatenate existing and newly mapped variable capacity data
    variable_capacity = pd.concat([var_cap_gen, keymap_varcap], axis=0).reset_index(drop=True)

    # Add operational cycles based on build years
    gen_build_costs = pd.read_csv(model_path + 'gen_build_costs.csv')
    gen_build_costs = gen_build_costs.groupby('GENERATION_PROJECT').agg({'build_year': 'min'}).reset_index()

    variable_capacity = pd.merge(variable_capacity, gen_build_costs, on="GENERATION_PROJECT")
    variable_capacity['cycle'] = variable_capacity['build_year'] - 2023

    return variable_capacity[['GENERATION_PROJECT', 'timepoint_id', 'gen_max_capacity_factor', 'cycle']]

# Function to generate future variable capacity factors by cycling timepoints
def generate(model_path, variable_capacity, cycles):
    """
    Generate future variable capacity factors by extending timepoints.

    Args:
        model_path (str): Path to the model directory.
        variable_capacity (pd.DataFrame): Base year variable capacity data.

    Returns:
        None
    """
    var_caps = []

    # Generate future data by cycling through 3 operational periods
    for i in range(cycles):
        new_var = variable_capacity.copy()
        new_var['timepoint_id'] += i * 192
        new_var['skip'] = new_var['cycle'] - i
        var_caps.append(new_var)

    # Concatenate all periods and filter valid entries
    extended_variable_capacity = pd.concat(var_caps).reset_index(drop=True)
    extended_variable_capacity = extended_variable_capacity[extended_variable_capacity['skip'] <= 0]
    extended_variable_capacity = extended_variable_capacity[['GENERATION_PROJECT', 'timepoint_id', 'gen_max_capacity_factor']]

    # Save the extended data to a CSV file
    extended_variable_capacity.to_csv(model_path + 'variable_capacity_factors.csv', index=False)
    print('Variable Capacity Factors saved in ../../model/inputs/variable_capacity_factors.csv')

    return extended_variable_capacity