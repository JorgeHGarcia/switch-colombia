import pandas as pd

def table(model_outputs_path, model_inputs_path):
    new_gen = pd.read_csv(model_outputs_path+'BuildGen.csv')
    new_gen = new_gen[new_gen['GEN_BLD_YRS_2'] >= 2023]
    new_gen = new_gen[new_gen['BuildGen'] > 1]

    gen_info = pd.read_csv(model_inputs_path+'gen_info.csv')
    new_gen = pd.merge(new_gen, gen_info,
                        left_on='GEN_BLD_YRS_1',right_on='GENERATION_PROJECT',how='inner')

    new_gen = new_gen.groupby(['gen_tech','GEN_BLD_YRS_2']).agg({
        'BuildGen' : 'sum'}).reset_index()
    new_gen.rename(columns={'GEN_BLD_YRS_2': 'Year'}, inplace=True)
    new_gen['BuildGen'] = new_gen['BuildGen'].round(2)

    pivot_table = new_gen.pivot_table(index='gen_tech',columns='Year',
                                    values='BuildGen',aggfunc='sum').fillna(0)
    pivot_table.rename(columns={'gen_tech': 'Technology'}, inplace=True)
    pivot_table.loc['Total'] = pivot_table.sum()

    return pivot_table

import plotly.express as px
def dispatched_generation(dataframe, x_axis, y_axis, color):
    dataframe = dataframe.groupby([x_axis, color]).agg({
        y_axis : 'sum'}).reset_index()
    dataframe = dataframe.sort_values(by=y_axis, ascending=False)
    fig = px.bar(
        dataframe, x=x_axis, y=y_axis,
        color=color, title='Generation Dispatch Over Time by Technology',
        labels={y_axis: 'Dispatched Generation (MW)', x_axis: 'Year'})

    unique_years = dataframe[x_axis].unique()
    # Update layout for better readability if needed
    fig.update_layout(barmode='stack', xaxis_title="Timestamp", xaxis=dict(
        tickvals=unique_years,
        tickangle=-45,
        tickfont=dict(size=10),  # Adjust the font size for better fit
        showgrid=True  # Show grid to help align the labels visually
        ),
        yaxis_title="Dispatched Generation (TWh)")
    fig.show()

def annual_emmissions(dataframe, x_axis, y_axis):
    fig = px.bar(
        dataframe, x=x_axis, y=y_axis,
        labels={y_axis: 'Annual Emissions (MtCO2)', x_axis: 'Year'},
        text=y_axis)
    # Mejorar la visualización
    fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(xaxis=dict(tickvals=dataframe[x_axis].to_list()))
    fig.show()

from plotly.subplots import make_subplots
def installed_capacity(esc0, escf):
    # Create individual figures
    fig1 = px.pie(esc0, names='gen_tech', values='BuildGen', title='Generation Reported (XM)')
    fig2 = px.pie(escf, names='gen_tech', values='BuildGen', title='Generation Predicted (Switch)')

    # Create subplots with the 'type' argument set to 'domain' to accommodate pie charts
    fig = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]], 
                        subplot_titles=("2023", "2037"))

    # Add figures to the subplots
    for trace in fig1.data: fig.add_trace(trace, row=1, col=1)
    for trace in fig2.data: fig.add_trace(trace, row=1, col=2)

    # Ensure legend items show only once
    names = set()
    for trace in fig.data:
        if (trace.name in names): trace.showlegend = False
        else: names.add(trace.name)

    # Show the figure
    fig.show()