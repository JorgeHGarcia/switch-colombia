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
        ['GENERATION_PROJECT', 'gen_energy_source', 'gen_load_zone']]

    # Create variable capacity IDs for missing projects
    missing_var_cap['var_cap_id'] = missing_var_cap['gen_energy_source'] + missing_var_cap['gen_load_zone']
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
def generate(model_path, variable_capacity, period, cycles):
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
        new_var['skip'] = new_var['cycle'] - i*period
        var_caps.append(new_var)

    # Concatenate all periods and filter valid entries
    extended_variable_capacity = pd.concat(var_caps).reset_index(drop=True)
    extended_variable_capacity = extended_variable_capacity[extended_variable_capacity['skip'] <= 0]
    extended_variable_capacity = extended_variable_capacity[['GENERATION_PROJECT', 'timepoint_id', 'gen_max_capacity_factor']]

    # Save the extended data to a CSV file
    extended_variable_capacity.to_csv(model_path + 'variable_capacity_factors.csv', index=False)
    print('Variable Capacity Factors saved in ../../model/inputs/variable_capacity_factors.csv')

    return extended_variable_capacity

import swcol as sw
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

def plot_variable_capacity(model_path, hydro_variable_capacity, timepoints):
    gen_info=pd.read_csv(model_path+'gen_info.csv')
    mean_vc = pd.merge(hydro_variable_capacity, timepoints, on='timepoint_id', how="inner")
    mean_vc = pd.merge(mean_vc, gen_info, on='GENERATION_PROJECT', how="inner")
    mean_vc = mean_vc[mean_vc['timepoint_id'] <= 192]

    mean_vc[['Year', 'Quarter', 'Type', 'Hour']] = mean_vc['timestamp'].str.extract(r'(\d{4})_(Q\d)_(\w+)_(\d+)h')
    mean_vc["Hour"] = mean_vc["Hour"].astype(int)
    mean_vc = mean_vc.sort_values(by=['Hour'])
    mean_vc = mean_vc[['gen_max_capacity_factor','gen_tech','Quarter','Type','Hour']]

    mean_vc = mean_vc.groupby(['Quarter','gen_tech','Type','Hour']).agg({
        'gen_max_capacity_factor': 'mean'
    }).reset_index()

    mean_vc['Quarter'] = mean_vc['Quarter'].replace({'Q1': 'Quarter 1', 'Q2': 'Quarter 2', 'Q3': 'Quarter 3', 'Q4': 'Quarter 4'})
    mean_lab_solar_vc = mean_vc[(mean_vc['gen_tech'] == 'pv_solar') & (mean_vc['Type'] == 'labor')]
    mean_lab_wind_vc = mean_vc[(mean_vc['gen_tech'] == 'Eolica') & (mean_vc['Type'] == 'labor')]
    mean_lab_hydro_vc = mean_vc[(mean_vc['gen_tech'] == 'Hidro') & (mean_vc['Type'] == 'labor')]
    mean_lab_river_vc = mean_vc[(mean_vc['gen_tech'] == 'RunOfRiver') & (mean_vc['Type'] == 'labor')]

    # Colores personalizados para cada quarter
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    quarter_order = ['Quarter 1', 'Quarter 2', 'Quarter 3', 'Quarter 4']
    color_map = dict(zip(quarter_order, colors))
    # Crear figura de subplots
    fig = make_subplots(
        rows=2, cols=2, shared_xaxes=False, shared_yaxes=False, vertical_spacing=0.15,
        subplot_titles=["Solar - Labor Days", "Wind - Labor Days","Hydro (<20 MW) - Labor Days","Run of River (<20 MW) - Labor Days"],
    )
    # Función para agregar trazos
    def add_traces(fig, data, row, col):
        quarters = data['Quarter'].unique()
        for quarter in quarters:
            subset = data[data['Quarter'] == quarter]
            fig.add_trace(
                go.Scatter(
                    x=subset['Hour'],
                    y=subset['gen_max_capacity_factor'],
                    mode='lines+markers',
                    name=quarter,  # Solo el quarter como nombre
                    legendgroup=quarter,  # Agrupar leyenda por quarter
                    showlegend=(col == 1 and row == 1),  # Mostrar la leyenda solo en la primera columna
                    line=dict(color=color_map.get(quarter, '#000000'))  # Color personalizado
                ),
                row=row, col=col
            )
    # Agregar datos
    add_traces(fig, mean_lab_solar_vc, row=1, col=1)
    add_traces(fig, mean_lab_wind_vc, row=1, col=2)
    add_traces(fig, mean_lab_hydro_vc, row=2, col=1)
    add_traces(fig, mean_lab_river_vc, row=2, col=2)

    # Layout general
    fig.update_layout(
        height=9*80, width=16*50,
        title_text="Variable Capacity Factors",
        template="plotly_white",
        legend=dict(
            orientation="h",
            y=-0.1, x=0.5,
            xanchor='center'
        ),
        font_family="Arial", font_size=14
    )

    # Configurar ejes
    fig.update_xaxes(dtick=2, row=1)
    fig.update_xaxes(dtick=2, title_text="Hours", row=2)
    fig.update_yaxes(title_text="Capacity Factors [%]", col=1)
    fig.update_yaxes(range=[0, 1])

    fig.write_image("../images/Mean Capacity Factors (Wind - Solar).png")
    fig.show()

def plot_all_capacities(model_path, hydro_variable_capacity, timepoints, base_year):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template

    gen_info=pd.read_csv(model_path+'gen_info.csv')
    plot_var_cap = pd.merge(hydro_variable_capacity, timepoints, on='timepoint_id', how="inner")
    plot_var_cap = pd.merge(plot_var_cap, gen_info, on='GENERATION_PROJECT')

    plot_var_cap['Tech'] = plot_var_cap['gen_tech'].replace(parse_tech)
    plot_var_cap['Tech'] = pd.Categorical(plot_var_cap['Tech'], categories=['Hydro', 'Run of River', 'Solar', 'Wind'], ordered=True)

    plot_var_cap = plot_var_cap[
        ['GENERATION_PROJECT', 'Tech', 'timepoint_id', 'gen_max_capacity_factor', 'timestamp', 'timeseries']].sort_values(by=['timepoint_id', 'Tech'])
    plot_var_cap['timestamp'] = plot_var_cap['timestamp'].str.replace(r'^\d{4}_', '', regex=True)

    project_color_map = plot_var_cap.drop_duplicates("GENERATION_PROJECT").set_index("GENERATION_PROJECT")["Tech"].map(tech_colors).to_dict()

    fig = px.line(
        plot_var_cap[plot_var_cap['timepoint_id'] <= 192],
        x="timestamp", y="gen_max_capacity_factor",
        title="Capacity Factors "+str(base_year),
        labels={"timestamp": "Timestamp", "gen_max_capacity_factor": "Capacity Factor", 'GENERATION_PROJECT':'Generation Projects'},
        color="GENERATION_PROJECT",
        color_discrete_map=project_color_map,
        height=9*50, width=16*50,
        template="plotly_white"
    )
    fig.update_layout(yaxis=dict(range=[0, 1]))
    fig.update_xaxes(dtick=6)
    fig.show()