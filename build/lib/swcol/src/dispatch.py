import pandas as pd
import swcol as sw
import plotly.express as px

def plot_dispatch_vs_demand(demand_x_dispatch, columns):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    fig = px.line(
    demand_x_dispatch,
    x='timestamp',
    y=columns,
    color_discrete_sequence=[colors[0], colors[1]],
    labels={'value': 'Value (MW)', 'variable': 'Series'},
    height=9*50, width=16*50,
    template='plotly_white')
    
    fig.show()