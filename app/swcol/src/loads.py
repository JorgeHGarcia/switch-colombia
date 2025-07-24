import pandas as pd
import swcol as sw
def cluster(generation):
    # Clustering: Aplicar la función para obtener el cuartil y combinar con el año
    generation['Date'] = pd.to_datetime(generation['Date'])
    generation = sw.rain_seasons.format_hours(generation)

    generation = generation.groupby(['timestamp','Tech']).agg({
        'GeneReal': 'mean'}).reset_index()
    print("Shape Gene_Recurso (Melted, Group by Tech, Timestamp):",generation.shape)
    #gene_melted.to_csv(dema_path+'Melted_Gen_Res.csv')
    return generation

import plotly.express as px
def plot_multiple_line(generation, sort, x, y, color, title, labels, frec=36):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    generation = generation.sort_values(by=sort)
    fig = px.line(
        generation, 
        x=x, y=y, 
        color_discrete_sequence=colors,
        title=title,
        color=color,
        labels=labels,
        height=9*50, width=16*50,
        template='plotly_white'
    )
    fig.update_xaxes(dtick=frec)
    fig.show()

from plotly.subplots import make_subplots
def plot_clusterized_loads(loads, year='2023'):
    loads_year = loads[loads['timestamp'].str.contains(year)].copy()
    loads_year['Zone'] = loads_year['Zone'].replace({'Surocciden': 'Suroccidente'})
    loads_year_labors = loads_year[loads_year['timestamp'].str.contains("labor")].sort_values(by='Date').copy()
    loads_year_labors['timestamp'] = loads_year_labors['timestamp'].str.replace(r'^\d{4}_(Q\d)_labor_(\d+h)$', r'\1_\2', regex=True)
    loads_year_holiday = loads_year[loads_year['timestamp'].str.contains("holidays")].sort_values(by='Date').copy()
    loads_year_holiday['timestamp'] = loads_year_holiday['timestamp'].str.replace(r'^\d{4}_(Q\d)_holidays_(\d+h)$', r'\1_\2', regex=True)

    parse_tech, colors, tech_order, tech_colors = sw.template.get()
    # Create individual plots
    fig1 = px.line(loads_year_labors, x='timestamp', y='demand_mw', color='Zone', color_discrete_sequence=colors, title='Labors')
    fig2 = px.line(loads_year_holiday, x='timestamp', y='demand_mw', color='Zone', color_discrete_sequence=colors, title='Holidays')

    # Create subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Labor days", "Holidays"))
    # Add figures to subplots
    for trace in fig1['data']:
        fig.add_trace(trace, row=1, col=1)
    for trace in fig2['data']:
        fig.add_trace(trace, row=1, col=2)

    # Only show one legend
    names = set()
    for trace in fig['data']:
        if (trace.name in names): trace.showlegend = False
        else: names.add(trace.name)

    fig.update_layout(
        title='Clustered Load Curves by Zone in '+year,
        height=9*50, width=16*50, template="plotly_white",
        yaxis=dict(range=[0, 4000], title='Demand [MWh]'),
        yaxis2=dict(range=[0, 4000]),
        legend=dict(
            orientation="h",
            y=-0.3, x=0.5,
            xanchor='center'
        ),
        font_family="Arial", font_size=14
    )

    fig.update_xaxes(dtick=6, row=1, col=1)
    fig.update_xaxes(dtick=6, row=1, col=2)
    fig.write_image("../images/Clustered Load Curves by Zone in "+year+".png")
    fig.show()

# Plot transmision lines
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from shapely.geometry import LineString
from mpl_toolkits.axes_grid1 import make_axes_locatable
def plot_transmission_lines(transmission_lines, zones, zones_points):
    #Mapa redes
    # Create LineString geometries for transmission lines
    lines_geometry = []
    for index, row in transmission_lines.iterrows():
        start_point = zones_points[zones_points['Zone'] == row['trans_lz1']]['geometry'].values[0]
        end_point = zones_points[zones_points['Zone'] == row['trans_lz2']]['geometry'].values[0]
        lines_geometry.append(LineString([start_point, end_point]))

    # Create a GeoDataFrame for transmission lines
    lines_gdf = gpd.GeoDataFrame(transmission_lines, geometry=lines_geometry)

    # Explicitly set min and max values for 'existing_trans_cap'
    min_existing_trans_cap = 500
    max_existing_trans_cap = 1400

    # Normalize the values of 'existing_trans_cap' based on min and max
    lines_gdf['normalized_existing_trans_cap'] = Normalize(vmin=min_existing_trans_cap, vmax=max_existing_trans_cap)(lines_gdf['existing_trans_cap'])

    # Plot the zones' polygons
    fig, ax = plt.subplots(figsize=(10, 10))

    # Plot zones' polygons (excluding "Extra")
    zones[~zones['Zone'].str.contains('Extra')].plot(ax=ax, color='#ffffff', edgecolor='black', linewidth=0.5)
    # Plot zones' polygons for "Extra"
    zones[zones['Zone'] == 'Extra'].plot(ax=ax, color='#ffffff', edgecolor='black', linewidth=0.5, alpha=0.7)

    # Plot transmission lines between centroids with normalized color mapping
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)

    from matplotlib.colors import LinearSegmentedColormap
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    lines_gdf.plot(ax=ax, linewidth=8, cmap=LinearSegmentedColormap.from_list("cmap", [colors[3], colors[1]]), alpha=0.7, column='normalized_existing_trans_cap', legend=True, cax=cax)

    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)

    # Set colorbar labels and ticks
    cax.set_ylabel("Transmission Capacity [MWh]", fontsize=14)
    cax.set_yticklabels([f'{val:.0f}' for val in [min_existing_trans_cap, max_existing_trans_cap]])
    cax.yaxis.set_ticks([0, 1])  # Normalize the ticks

    # Add zone names on top of each area (excluding "Extra")
    zones['Zone'] = zones['Zone'].replace({'Surocciden': 'Suroccidente'})
    for idx, row in zones.iterrows():
        if row['Zone'] != 'Extra':
            ax.annotate(row['Zone'], (row['geometry'].centroid.x, row['geometry'].centroid.y),
                ha='center', va='center', color='black', fontsize=12)


    # Show the plot
    plt.show()

# Replace with new year
def replace_year(timestamp, new_year):
    new_timestamp = str(new_year) + str(timestamp)[4:]
    return pd.Timestamp(new_timestamp)

# Generate loads by Periods
def generate_by_periods(XM_report, load_type, base_year, grow_rate, period, cycles):
    loads = XM_report[['Date',load_type]]
    last_year = loads['Date'].iloc[-1].year
    if (last_year != base_year):
        print("Error: Base year doesn't match with XM_Report")
        return
    next_year = last_year + period
    loads_future = loads.copy()
    for i in range(cycles-1):
        # Replace only year
        loads_future['Date'] = loads_future['Date'].apply(replace_year, args=(next_year,))
        loads_future[load_type] = loads_future[load_type] * ((1+grow_rate)**period)

        #print(f'The year is: {next_year}')
        loads = pd.concat([loads, loads_future], axis=0)

        next_year += period
        loads_future = loads_future.copy()

    # Reset Dataframe
    loads.reset_index(drop=True, inplace=True)

    loads = loads.rename(columns={load_type: 'Load'})
    return loads

import pandas as pd
from tqdm.notebook import tqdm
def generate_by_zones(loads, zone_consume_perc):
    # Convert to perentages
    zone_consume_perc['Proportion'] = zone_consume_perc['Value'] / 100
    # Store results
    res = []
    # Iterar sobre las filas de ventas y distribuir por zonas
    for _, load_row in tqdm(loads.iterrows(), total=loads.shape[0], desc="Processing Files"):
        for _, zone_row in zone_consume_perc.iterrows():
            zone_loads = load_row['Load'] * zone_row['Proportion']
            res.append({
                'Date': load_row['Date'],
                'Zone': zone_row['Zone'],
                'Load': zone_loads
            })
    
    res = pd.DataFrame(res)
    res['demand_mw'] = round(res['Load'] / 1000, 2)
    res = res.drop(columns=['Load'])
    return res

def loads_to_timestamps(loads):
    loads = loads.groupby(['Date','Zone']).agg({
        'demand_mw': 'sum'
    }).reset_index()

    loads['Date'] = pd.to_datetime(loads['Date'])
    loads = sw.rain_seasons.format_hours(loads)

    loads = loads.groupby(['timestamp','Zone']).agg({
        'demand_mw': 'mean',
        'Date': 'max'
    }).reset_index()
    return loads

def melt_xm(path):
    """
    Args:
        path string: Path to DemaReal_Sistema.csv, DemaCome_Sistema.csv, Gene_Sistema.csv, GeneIdea_Sistema.csv

    Returns dataframe: Merged columns [Date, DemaReal_Sistema, DemaCome_Sistema, Gene_Sistema, GeneIdea_Sistema, timestamp]
    """
    # GetData
    DemaReal = pd.read_csv(path+'DemaReal_Sistema.csv')
    DemaReal = DemaReal.drop(DemaReal.columns[0], axis=1) # Drop Unnamed Column
    DemaCome = pd.read_csv(path+'DemaCome_Sistema.csv')
    DemaCome = DemaCome.drop(DemaCome.columns[0], axis=1) # Drop Unnamed Column
    Gene = pd.read_csv(path+'Gene_Sistema.csv')
    Gene = Gene.drop(Gene.columns[0], axis=1) # Drop Unnamed Column
    GeneIdea = pd.read_csv(path+'GeneIdea_Sistema.csv')
    GeneIdea = GeneIdea.drop(GeneIdea.columns[0], axis=1) # Drop Unnamed Column

    # Melt tables
    DemaReal = pd.melt(DemaReal.iloc[:,2:], id_vars=['Date'], var_name='Hora', value_name='DemaReal_Sistema')
    DemaCome = pd.melt(DemaCome.iloc[:,2:], id_vars=['Date'], var_name='Hora', value_name='DemaCome_Sistema')
    Gene = pd.melt(Gene.iloc[:,2:], id_vars=['Date'], var_name='Hora', value_name='Gene_Sistema')
    GeneIdea = pd.melt(GeneIdea.iloc[:,2:], id_vars=['Date'], var_name='Hora', value_name='GeneIdea_Sistema')

    # Merge Tables
    XM_report= pd.merge(DemaReal, DemaCome, on=['Date', 'Hora'])
    XM_report = pd.merge(XM_report, Gene, on=['Date', 'Hora'])
    XM_report = pd.merge(XM_report, GeneIdea, on=['Date', 'Hora'])

    XM_report['Hora'] = XM_report['Hora'].apply(sw.rain_seasons.extract_hour)
    XM_report['Date'] = XM_report['Date'].astype(str)
    XM_report['Date'] = XM_report['Date'] + ' ' + XM_report['Hora']
    # Delete column "Hora"
    XM_report = XM_report.drop(columns=['Hora'])
    # Transform into timestamps
    XM_report = sw.rain_seasons.format_hours(XM_report)
    
    XM_report = XM_report.sort_values(by='Date')
    XM_report = XM_report.reset_index(drop=True)

    return XM_report

# Generation by Resource
def add_tech(dema_path):
    generation = pd.read_csv(dema_path+'Gene_Recurso.csv')
    generation = generation.drop(generation.columns[:2], axis=1) # Remove the ID column
    print("Shape Gene_Recurso:",generation.shape)

    ListResour = pd.read_csv(dema_path+'LitadoRecursos_Sistema.csv')
    ListResour = ListResour[['Values_Code','Values_Type','Values_RecType']]
    print("Shape LitadoRecursos_Sistema:",ListResour.shape)

    # Add 'Values_Type'(Tech) Column
    generation = pd.merge(generation, ListResour,
                          left_on="Values_code", right_on="Values_Code", how="inner")
    generation = generation.drop(columns=['Values_code','Values_Code'])

    return generation

def melt_dates(generation):
    generation = pd.melt(generation, id_vars=['Date','Values_Type','Values_RecType'], var_name='Hora', value_name='GeneReal')
    generation = generation.dropna()# Convert Values into MW
    generation['GeneReal'] = generation['GeneReal'] / 1000
    generation['Hora'] = generation['Hora'].apply(sw.rain_seasons.extract_hour)
    generation['Date'] = generation['Date'].astype(str)
    generation['Date'] = generation['Date'] + ' ' + generation['Hora']
    # Delete column "Hora"
    generation = generation.drop(columns=['Hora'])

    print("Shape Gene_Recurso (Melted):",generation.shape)
    # Group by Tech
    generation = generation.groupby(['Date','Values_Type','Values_RecType']).agg({'GeneReal': 'sum'}).reset_index()
    generation = generation.rename(columns={'Values_Type': 'Technology','Values_RecType': 'Tech_Type'})
    print("Shape Gene_Recurso (Melted, Group by Tech):",generation.shape)

    return generation