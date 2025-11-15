import pandas as pd
import swcol as sw
import plotly.express as px

def plot_dispatch_vs_demand(demand_x_dispatch, title, columns):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    fig = px.line(
    demand_x_dispatch,
    x='timestamp',
    y=columns,
    color_discrete_sequence=[colors[0], colors[1], colors[2], colors[3], colors[4]],
    labels={'value': 'Value [MW]', 'variable': 'Series'},
    height=9*50, width=16*50,
    template='plotly_white',
    title=title)
    
    fig.show()

def plot_line(dataframe, title, labels):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    fig = px.line(
    dataframe,
    x='timestamp', y='DispatchGen_MW',
    color='Tech', title=title,
    color_discrete_map=tech_colors,
    category_orders={"Tech": tech_order},
    labels=labels,
    height=9*50, width=16*50,
    template='plotly_white',
    )
    fig.update_xaxes(dtick=6)
    fig.show()

def plot_sankey(dispatch_tx, model_inputs_path, model_outputs_path):
    # Load transmission_dispatch from plants
    dispatch_tx_zn = dispatch_tx.groupby(['TRANS_TIMEPOINTS_1']).agg({
        'DispatchTx' : 'sum' }).reset_index()
    # Load dispatch from plant
    dispatch_pl = pd.read_csv(model_outputs_path+'dispatch.csv')
    dispatch_pl = dispatch_pl.groupby(['generation_project']).agg({
        'DispatchGen_MW' : 'sum' }).reset_index()
    # Get zone
    pl_zone = pd.read_csv(model_inputs_path+'gen_info.csv')
    pl_zone = pl_zone[['GENERATION_PROJECT', 'gen_load_zone']]
    dispatch_pl = pd.merge(dispatch_pl, pl_zone,
                        left_on='generation_project', right_on='GENERATION_PROJECT', how='inner')
    dispatch_pl = dispatch_pl.groupby(['gen_load_zone']).agg({
        'DispatchGen_MW' : 'sum' }).reset_index()

    # Substract transmission from total to get own dispatch
    dispatch_pl = pd.merge(dispatch_pl, dispatch_tx_zn,
                        left_on='gen_load_zone', right_on='TRANS_TIMEPOINTS_1', how='inner')
    dispatch_pl['DispatchTx'] = dispatch_pl['DispatchGen_MW'] - dispatch_pl['DispatchTx']
    dispatch_pl['TRANS_TIMEPOINTS_2'] = dispatch_pl['TRANS_TIMEPOINTS_1']

    dispatch_pl = dispatch_pl[['TRANS_TIMEPOINTS_1','TRANS_TIMEPOINTS_2', 'DispatchTx']]
    # Concat inner dispatch
    dispatch_tx = pd.concat([dispatch_tx, dispatch_pl])

    # Get indices from Zones for plot
    labels = pd.read_csv(model_inputs_path+'load_zones.csv')['LOAD_ZONE'].tolist()

    # Transform TRANS_TIMEPOINTS_1 column into indices
    dispatch_tx['TRANS_TIMEPOINTS_1'] = pd.Categorical(
        dispatch_tx['TRANS_TIMEPOINTS_1'], categories=labels).codes
    # Transform TRANS_TIMEPOINTS_2 column into indices
    dispatch_tx['TRANS_TIMEPOINTS_2'] = len(labels) + pd.Categorical(
        dispatch_tx['TRANS_TIMEPOINTS_2'], categories=labels).codes

    labels.extend(labels)

    import plotly.graph_objects as go
    # Extract columns from the DataFrame
    source = dispatch_tx["TRANS_TIMEPOINTS_1"].tolist()
    target = dispatch_tx["TRANS_TIMEPOINTS_2"].tolist()
    value = dispatch_tx["DispatchTx"].tolist()

    # Define colors for nodes
    node_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    node_colors.extend(node_colors)

    # Function to generate soft random colors
    import random
    def generate_color():
        r = random.randint(150, 255)  # Red component (light)
        g = random.randint(150, 255)  # Green component (light)
        b = random.randint(150, 255)  # Blue component (light)
        a = 0.6
        return f"rgba({r}, {g}, {b}, {a})"

    # Generate soft random colors for links
    link_colors = [generate_color() for _ in range(len(source))]

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,  # Space between nodes
            thickness=20,  # Thickness of nodes
            line=dict(color="black", width=0.5),
            label=labels, color=node_colors
        ),
        link=dict(
            source=source,  # Indices of the source nodes
            target=target,  # Indices of the target nodes
            value=value,    # Values of the links
            color=link_colors  # Assign colors to links
        ))])

    # Add annotations and styling
    fig.update_layout(
        annotations=[
            dict(
                x=0, y=1.1,
                xref="paper", yref="paper", text="Sources",
                showarrow=False, font=dict(size=14, color="black")
            ),
            dict(
                x=1, y=1.1,
                xref="paper", yref="paper", text="Targets",
                showarrow=False, font=dict(size=14, color="black")
            )],        
        height=9*50, width=16*50,
        template="plotly_white"
    )

    # Show the figure
    fig.show()


import plotly.graph_objects as go
import ipywidgets as widgets
from IPython.display import display
def plot_sankey_timestamp(dispatch_tx, timepoints, model_inputs_path, model_outputs_path):
    # Define colors for nodes
    node_colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    node_colors.extend(node_colors)
    # Function to generate soft random colors
    import random
    def generate_color():
        r = random.randint(150, 255)  # Red component (light)
        g = random.randint(150, 255)  # Green component (light)
        b = random.randint(150, 255)  # Blue component (light)
        a = 0.6
        return f"rgba({r}, {g}, {b}, {a})"

    dispatch_tx = dispatch_tx.merge(timepoints, left_on='TRANS_TIMEPOINTS_3', right_on='timepoints', how='inner')
    dispatch_tx = dispatch_tx[['TRANS_TIMEPOINTS_1', 'TRANS_TIMEPOINTS_2', 'timestamp', 'DispatchTx']]

    dispatch_tx_zn = dispatch_tx.groupby(['TRANS_TIMEPOINTS_1', 'timestamp'])['DispatchTx'].sum().reset_index()
    dispatch_tx_zn['merge'] = dispatch_tx_zn['TRANS_TIMEPOINTS_1'] + dispatch_tx_zn['timestamp']
    dispatch_tx_zn.drop(columns=['timestamp'], inplace=True)

    # Load and preprocess plant dispatch data
    dispatch_pl = pd.read_csv(model_outputs_path + 'dispatch.csv')
    dispatch_pl = dispatch_pl.groupby(['gen_load_zone', 'timestamp'])['DispatchGen_MW'].sum().reset_index()
    dispatch_pl['merge'] = dispatch_pl['gen_load_zone'] + dispatch_pl['timestamp']

    dispatch_pl = dispatch_pl.merge(dispatch_tx_zn, on='merge', how='inner')
    dispatch_pl['DispatchTx'] = dispatch_pl['DispatchGen_MW'] - dispatch_pl['DispatchTx']
    dispatch_pl['TRANS_TIMEPOINTS_1'] = dispatch_pl['gen_load_zone']
    dispatch_pl['TRANS_TIMEPOINTS_2'] = dispatch_pl['gen_load_zone']
    dispatch_pl = dispatch_pl[['TRANS_TIMEPOINTS_1', 'TRANS_TIMEPOINTS_2', 'timestamp', 'DispatchTx']]

    dispatch_tx = pd.concat([dispatch_tx, dispatch_pl])

    # Parse custom timestamps
    def parse_custom_timestamp(ts):
        try:
            year, quarter, hour = int(ts.split('_')[0]), int(ts.split('_')[1][1:]), int(ts.split('_')[-1].replace('h', ''))
            return pd.Timestamp(year=year, month=(quarter - 1) * 3 + 1, day=1, hour=hour)
        except:
            return pd.NaT

    dispatch_tx['parsed_timestamp'] = dispatch_tx['timestamp'].apply(parse_custom_timestamp)
    dispatch_tx.dropna(subset=['parsed_timestamp'], inplace=True)

    dispatch_tx = dispatch_tx.groupby(['TRANS_TIMEPOINTS_1', 'TRANS_TIMEPOINTS_2', 'parsed_timestamp'])['DispatchTx'].sum().reset_index()

    # Create widgets for filtering
    unique_dates = sorted(dispatch_tx['parsed_timestamp'].dt.to_period('M').unique())
    unique_hours = sorted(dispatch_tx['parsed_timestamp'].dt.hour.unique())

    date_dropdown = widgets.Dropdown(options=[str(d) for d in unique_dates], description='Year-Month:')
    hour_dropdown = widgets.Dropdown(options=unique_hours, description='Hour:')
    run_button = widgets.Button(description="Update Sankey")

    # Display widgets
    display(date_dropdown, hour_dropdown, run_button)

    # Define the button click callback
    def on_button_click(b):
        date_str = date_dropdown.value
        hour = hour_dropdown.value
        print("saw")
        
        selected_date = pd.Period(date_str)
        filtered_df = dispatch_tx[(dispatch_tx['parsed_timestamp'].dt.to_period('M') == selected_date) &
                                (dispatch_tx['parsed_timestamp'].dt.hour == hour)].copy()
        if filtered_df.empty:
            print(f"No data available for {date_str} at hour {hour}")
            return
        
        labels = pd.read_csv(model_inputs_path + 'load_zones.csv')['LOAD_ZONE'].tolist()
        filtered_df['TRANS_TIMEPOINTS_1'] = pd.Categorical(filtered_df['TRANS_TIMEPOINTS_1'], categories=labels).codes
        filtered_df['TRANS_TIMEPOINTS_2'] = len(labels) + pd.Categorical(filtered_df['TRANS_TIMEPOINTS_2'], categories=labels).codes
        labels.extend(labels)

        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=15, thickness=20, color=node_colors, line=dict(color='black', width=0.5), label=labels),
            link=dict(source=filtered_df['TRANS_TIMEPOINTS_1'], target=filtered_df['TRANS_TIMEPOINTS_2'],
                    value=filtered_df['DispatchTx'], color=[generate_color() for _ in range(len(filtered_df))])
        )])

        fig.update_layout(title_text=f"Transmission Dispatch for {date_str} at {hour:02d}:00",
                        height=9*50, width=16*50, template="plotly_white")
        fig.show()

    # Connect the button to the function
    run_button.on_click(on_button_click)

from plotly.subplots import make_subplots
def plot_base_year_comparission(gen_res, gen_disp, base_year='2023'):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template

    # Take both Sets
    gen_res = gen_res[['timestamp', 'Tech', 'DispatchGen_MW', ]]
    gen_disp = gen_disp[gen_disp['timestamp'].str.startswith(base_year)][['timestamp', 'Tech', 'DispatchGen_MW']]
    # Crete individual plots
    fig1 = px.line(
        gen_res, x='timestamp', y='DispatchGen_MW', color='Tech', title='Generation Reported (XM)',
        color_discrete_map=tech_colors, category_orders={"Tech": tech_order})
    fig2 = px.line(
        gen_disp, x='timestamp', y='DispatchGen_MW', color='Tech', title='Generation Predicted (Switch)',
        color_discrete_map=tech_colors, category_orders={"Tech": tech_order})

    # Create subplots
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Generation Reported (XM)", "Generation Predicted (Switch)"))
    # Add figures to subplots
    for trace in fig1['data']: fig.add_trace(trace, row=1, col=1)
    for trace in fig2['data']: fig.add_trace(trace, row=1, col=2)

    # Only show one legend
    names = set()
    for trace in fig['data']:
        if (trace.name in names): trace.showlegend = False
        else: names.add(trace.name)

    # Add buttons to change y-range
    fig.update_layout(
        title='Base Year ('+base_year+')',
        updatemenus=[
            go.layout.Updatemenu(
                buttons=list([
                    dict(args=[{"yaxis.autorange": True, "yaxis2.autorange": True}], label="Auto", method="relayout"),
                    dict(args=[{"yaxis.range": [5, 30], "yaxis2.range": [5, 30]}], label="30 Fixed", method="relayout"),
                    dict(args=[{"yaxis.range": [0, 700], "yaxis2.range": [0, 700]}], label="700 Fixed", method="relayout"),
                    dict(args=[{"yaxis.range": [0, 9000], "yaxis2.range": [0, 9000]}], label="9k Fixed", method="relayout")]),
                direction="down", x=1.2, xanchor="right", y=1.2
            )],
        height=9*50, width=16*50,
        template="plotly_white")

    fig.update_xaxes(dtick=12, row=1, col=1)
    fig.update_xaxes(dtick=12, row=1, col=2)
    fig.show()


"""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_q1_generation(gen_res, gen_disp, tech_colors, tech_order):   
    # Exctract Quarter, daytime, hour
    for df in [gen_res, gen_disp]:
        df['Quarter'] = df['timestamp'].str.extract(r'Q([1-4])')[0].apply(lambda x: f'Q{x}')
        df['DayType'] = df['timestamp'].str.extract(r'_(L|H)_')[0].map({'L': 'Labor', 'H': 'Holiday'})
        df['Hour'] = df['timestamp'].str.extract(r'_(\d{1,2})h$')[0].astype(int)
    
    daytypes = ['Labor', 'Holiday']
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Q1 Labor - Reported (UPME)", "Q1 Holiday - Reported (UPME)",
            "Q1 Labor - Simulated (Switch)", "Q1 Holiday - Reportado Simulated (Switch)"],
        shared_yaxes=True
    )    
    # Map
    position_map = {
        ('Labor', 'Pred'): (1, 1),
        ('Holiday', 'Pred'): (1, 2),
        ('Labor', 'Real'): (2, 1),
        ('Holiday', 'Real'): (2, 2),
    }
    
    for daytype in daytypes:
        # Predicated Data
        disp_df = gen_disp[(gen_disp['DayType'] == daytype) & (gen_disp['Quarter'] == 'Q1')]
        fig_pred = px.line(
            disp_df, x='Hour', y='DispatchGen_MW', color='Tech',
            color_discrete_map=tech_colors, category_orders={"Tech": tech_order}
        )
        for trace in fig_pred['data']:
            #trace.update(fill='tozeroy')
            fig.add_trace(trace, row=position_map[(daytype, 'Pred')][0], col=position_map[(daytype, 'Pred')][1])
        
        # Real data
        res_df = gen_res[(gen_res['DayType'] == daytype) & (gen_res['Quarter'] == 'Q1')]
        fig_real = px.line(
            res_df, x='Hour', y='DispatchGen_MW', color='Tech',
            color_discrete_map=tech_colors, category_orders={"Tech": tech_order}
        )
        for trace in fig_real['data']:
            #trace.update(fill='tozeroy')
            fig.add_trace(trace, row=position_map[(daytype, 'Real')][0], col=position_map[(daytype, 'Real')][1])
    
    # Hide duplicated legends
    names = set()
    for trace in fig['data']:
        if trace.name in names:
            trace.showlegend = False
        else:
            names.add(trace.name)
    
    # Layout final
    fig.update_layout(
        height=12*50, width=16*50,
        template="plotly_white"
    )
    fig.update_xaxes(dtick=3, showticklabels=True, title_text=None)
    fig.update_yaxes(showticklabels=True, title_text=None)
    fig.update_annotations(font=dict(size=11))
    
    fig.show()

plot_q1_generation(gen_res, gen_disp, tech_colors, tech_order)
"""
def plot_q1_generation(gen_res, gen_disp):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    for df in [gen_res, gen_disp]:
        df['Quarter'] = df['timestamp'].str.extract(r'Q([1-4])')[0].apply(lambda x: f'Q{x}')
        df['DayType'] = df['timestamp'].str.extract(r'_(L|H)_')[0].map({'L': 'Labor', 'H': 'Holiday'})
        df['Hour'] = df['timestamp'].str.extract(r'_(\d{1,2})h$')[0]+'h'
    
    daytypes = ['Labor', 'Holiday']
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Q1 Labor", "Q1 Holiday", "Q1 Labor", "Q1 Holiday"],
        shared_yaxes=True,
        vertical_spacing=0.22, horizontal_spacing=0.06
    )
    position_map = {
        ('Labor', 'Real'): (1, 1), ('Holiday', 'Real'): (1, 2),
        ('Labor', 'Pred'): (2, 1), ('Holiday', 'Pred'): (2, 2),
    }
    legend_shown = set()
    export_rows = []
    for daytype in daytypes:
        for tipo, source in [('Real', gen_res), ('Pred', gen_disp)]:
            df_source = source[(source['DayType'] == daytype) & (source['Quarter'] == 'Q1')]
            for tech in tech_order:
                df_tech = df_source[df_source['Tech'] == tech]
                show = tech not in legend_shown
                if show:
                    legend_shown.add(tech)
                fig.add_trace(
                    go.Scatter(
                        x=df_tech['Hour'],
                        y=df_tech['DispatchGen_MW'],
                        mode='lines',
                        name=tech,
                        stackgroup='one',
                        line_shape='linear',
                        legendgroup=tech,
                        showlegend=show,
                        line=dict(color=tech_colors.get(tech, '#333333')),
                        fillcolor=tech_colors.get(tech, '#333333')
                    ),
                    row=position_map[(daytype, tipo)][0],
                    col=position_map[(daytype, tipo)][1]
                )
                export_rows.append(
                    df_tech.assign(
                        DayType=daytype,
                        Source=tipo,
                        Subplot=f"{tipo}-{daytype}"
                    )
                )
    # Final Layout
    fig.update_layout(
        height=12*50, width=16*50,
        template="plotly_white",
        legend=dict(
            orientation="h",
            y=-0.1, x=0.5,
            xanchor='center'
        ),
        font_family="Arial", font_size=16
    )
    fig.add_annotation(
    text="Generation [MW]",
    xref="paper", yref="paper",
    x=-0.1, y=0.5,
    showarrow=False,
    textangle=-90)
    
    fig.update_xaxes(dtick=4, showticklabels=True, title_text=None)
    fig.update_yaxes(range=[-400, 12000])
    
    fig.add_annotation(
        text="Actual Generation (XM)",
        xref="paper", yref="paper",
        x=0.5, y=1.12,
        showarrow=False,
        font=dict(size=18, family="Arial"),
        xanchor="center"
    )
    fig.add_annotation(
        text="Simulated Generation (Switch)",
        xref="paper", yref="paper",
        x=0.5, y=0.49,
        showarrow=False,
        font=dict(size=18, family="Arial"),
        xanchor="center"
    )

    fig.write_image(f"../images/Q1_Generation (XM - Switch).png")
    df_export = pd.concat(export_rows)
    df_export.to_csv("../images/Q1_Generation (XM - Switch).csv", index=False)
    fig.show()

def plot_generation_per_typical_day(gen_res, gen_disp):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    # Agrupar y preparar los datos reales (XM)
    gen_res_grouped = gen_res.groupby(['Quarter', 'DayType', 'Tech'])['DispatchGen_MW'].sum().reset_index()
    gen_res_grouped['DispatchGW'] = gen_res_grouped['DispatchGen_MW'] / 1000

    # Agrupar y preparar los datos simulados (Switch)
    gen_disp_grouped = gen_disp.groupby(['Quarter', 'DayType', 'Tech'])['DispatchGen_MW'].sum().reset_index()
    gen_disp_grouped['DispatchGW'] = gen_disp_grouped['DispatchGen_MW'] / 1000

    # Crear una columna combinada para el eje X
    gen_res_grouped['Category'] = gen_res_grouped['Quarter'] + '-' + gen_res_grouped['DayType']
    gen_disp_grouped['Category'] = gen_disp_grouped['Quarter'] + '-' + gen_disp_grouped['DayType']

    # Orden consistente
    categories = ['Q1-Labor', 'Q1-Holiday', 'Q2-Labor', 'Q2-Holiday', 'Q3-Labor', 'Q3-Holiday', 'Q4-Labor', 'Q4-Holiday']
    sources = ['Hydro', 'Run of River', 'Thermal', 'Solar', 'Wind']

    # Crear subplots
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=("Actual Generation (XM)", "Simulated Generation (Switch)"))

    threshold = 20 # Giga
    # Agregar datos reales (XM)
    for source in sources:
        data = gen_res_grouped[gen_res_grouped['Tech'] == source]
        y = [data[data['Category'] == cat]['DispatchGW'].sum() for cat in categories]
        text = [f'{val:.1f}' if val >= threshold else '' for val in y]
        fig.add_trace(go.Bar(
            name=source,
            x=categories,
            y=y,
            text=text,
            texttemplate='%{text}',
            textposition='inside',
            insidetextanchor='middle',
            textangle=0,
            marker_color=tech_colors[source]
        ), row=1, col=1)

    # Agregar datos simulados (Switch)
    for source in sources:
        data = gen_disp_grouped[gen_disp_grouped['Tech'] == source]
        y = [data[data['Category'] == cat]['DispatchGW'].sum() for cat in categories]
        text = [f'{val:.1f}' if val >= threshold else '' for val in y]
        fig.add_trace(go.Bar(
            name=source,
            x=categories,
            y=y,
            text=text,
            texttemplate='%{text:.1f}', textposition='inside', insidetextanchor='middle', textangle=0,
            marker_color=tech_colors[source],
            showlegend=False  # evitar duplicar leyenda
        ), row=1, col=2)

    # Layout general
    fig.update_layout(
        barmode='stack',
        title_text='2023 Generation per Typical day',
        yaxis_title='Generation [GWh/day]',
        height=9*50, width=16*50,
        template='plotly_white',
        xaxis_tickangle=-90,
        xaxis2_tickangle=-90,
        legend_traceorder='normal',
        legend=dict(
            orientation="h", y=-0.4, x=0.5, xanchor='center'
        ),
        font=dict(family="Arial", size=14)
    )

    # Cambiar tamaño de títulos de subplots (accediendo a annotations)
    for annotation in fig['layout']['annotations']:
        annotation['font'] = dict(size=18)

    fig.write_image(f"../images/Anual_Generation_2023_(XM - Switch.png")
    fig.show()
    gen_disp_grouped.to_csv(f"../images/Anual_Generation_2023_Switch.csv")
    gen_res_grouped.to_csv(f"../images/Anual_Generation_2023_XM.csv")