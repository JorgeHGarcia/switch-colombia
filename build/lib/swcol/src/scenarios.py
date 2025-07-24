import pandas as pd
import swcol as sw

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
    new_gen.rename(columns={'gen_tech': 'Tech'}, inplace=True)

    pivot_table = new_gen.pivot_table(index='Tech',columns='Year',
                                    values='BuildGen',aggfunc='sum').fillna(0)
    pivot_table.loc['Total'] = pivot_table.sum()
    
    return pivot_table

import plotly.express as px
def dispatched_generation(dataframe, title, units, x_axis, y_axis, color, folder, scenario, threshold = 0, img_path='../../images'):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template
    # Change values on gen_tech to match Switch output
    dataframe[color] = dataframe[color].replace(parse_tech)
    dataframe = dataframe.groupby([x_axis, color]).agg({
        y_axis : 'sum'}).reset_index()
    dataframe = dataframe.sort_values(by=[x_axis,y_axis], ascending=[True,False])
    dataframe['text'] = dataframe[y_axis].apply(lambda val: f'{val:.2f}' if val >= threshold else '')
    fig = px.bar(
        dataframe, x=x_axis, y=y_axis,
        text='text',
        color=color, title=title+' Over Time by Technology ('+scenario+')',
        labels={y_axis: 'Dispatched Generation (MW)', x_axis: 'Year'},
        color_discrete_map=tech_colors,
        category_orders={"Tech": tech_order},
        height=9*60, width=16*50,
        template='plotly_white',)

    unique_years = dataframe[x_axis].unique()
    # Update layout for better readability if needed
    fig.update_layout(
        barmode='stack',
        xaxis_title="",
        xaxis=dict(
            tickvals=unique_years,
            tickangle=0,
            tickfont=dict(size=14, family='Arial'),
            showgrid=True
        ),
        yaxis_title=title+" ["+units+"/year]",
        legend=dict(
            orientation="h",
            y=-0.1,  x=0.5,
            xanchor='center'
        ),
        font_family="Arial",
        font_size=14,
        legend_title_text=None
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='inside',  insidetextanchor='middle', textangle=0)
    fig.show()
    fig.write_image(img_path+"/scenarios/"+folder+"/"+title+" "+scenario+".png")
    

import numpy as np
import plotly.graph_objects as go
def annual_emmissions(dataframe, x_axis, y_axis, folder, scenario, img_path='../../images'):
    parse_tech, colors, tech_order, tech_colors = sw.template.get()  # Template
    # Extraer datos
    x = dataframe[x_axis].values
    y = dataframe[y_axis].values
    # Crear figura
    fig = go.Figure()   
    # Añadir línea con texto
    fig.add_trace(go.Scatter(
        x=x, y=y, mode='lines+text',
        text=[f'{val:.2f}' for val in y],
        textposition='top center',
        textfont=dict(size=14, family='Arial'),
        line=dict(color=colors[0])
    ))
    # Layout
    fig.update_layout(
        template='plotly_white', showlegend=False, height=9*50, width=16*50,
        font=dict(size=16, family='Arial'),
        xaxis=dict(
            title='', 
            tickvals=x.tolist(),
            titlefont=dict(size=18, family='Arial'),
            tickfont=dict(size=14, family='Arial')
        ),
        yaxis=dict(
            title='Annual Emissions [MtCO2]', 
            range=[0, max(y) * 1.1],
            titlefont=dict(size=18, family='Arial'),
            tickfont=dict(size=14, family='Arial')
        ),
        title=dict(
            text='Annual Emissions Over Time (' + scenario + ')',
            font=dict(size=20, family='Arial')
        )
    )    
    fig.write_image(img_path+"/scenarios/"+folder+"/Annual Emissions Over Time "+scenario+".png")
    fig.show()

def annual_emissions_combined(dataframes, x_axis, y_axis, labels, colors, folder, title, img_path='../../images'):
    fig = go.Figure()

    for i, df in enumerate(dataframes):
        x = df[x_axis].values
        y = df[y_axis].values
        fig.add_trace(go.Scatter(
            x=x, y=y, mode='lines+text',
            name=labels[i],
            line=dict(color=colors[i])
        ))

    fig.update_layout(
        template='plotly_white', height=9*50, width=16*50,
        font=dict(size=16, family='Arial'),
        xaxis=dict(
            title='', 
            tickvals=sorted(set().union(*(df[x_axis] for df in dataframes))),
            titlefont=dict(size=18, family='Arial'),
            tickfont=dict(size=14, family='Arial')
        ),
        yaxis=dict(
            title='Emissions [MtCO<sub>2</sub>/Year]', 
            range=[0, max([df[y_axis].max() for df in dataframes]) * 1.1],
            titlefont=dict(size=16, family='Arial'),
            tickfont=dict(size=14, family='Arial')
        ),
        title=dict(
            text='Annual Emissions Over Time (' + title + ')',
            font=dict(size=20, family='Arial')
        ),
        showlegend=True,        
        legend=dict(
            orientation="h",
            y=-0.1, x=0.5,
            xanchor='center'
        )
    )

    fig.write_image(img_path+"/scenarios/" + folder + "/Annual Emissions Over Time " + title + ".png")
    fig.show()

def installed_capacity(esc0, escf, year0, yearf, scenario, model, img_path='../../images'):
    parse_tech, colors, tech_order, tech_colors = sw.template.get() # Template

    esc0['Tech'] = esc0['Tech'].replace(parse_tech)
    escf['Tech'] = escf['Tech'].replace(parse_tech)
    # Inside donut chart values
    labels_inner = esc0['Tech'].tolist()
    values_inner = esc0['BuildGen'].tolist()
    # Inner donut chart values
    label_inner = ['blank']
    value_inner = [100]
    color_inner = ['#FFFFFF']
    # Outer donut chart values
    labels_outer = escf['Tech'].tolist()
    values_outer = escf['BuildGen'].tolist()

    fig = go.Figure()
    # Inside ring
    fig.add_trace(go.Pie(
        labels=labels_inner, values=values_inner,
        hole=0.4, direction='clockwise', sort=True,
        marker=dict(colors=[tech_colors[label] for label in labels_inner]),
        textinfo='percent', textposition='inside', showlegend=True,
    domain=dict(x=[0.25, 0.75], y=[0.25, 0.75])
    ))
    # Inner ring
    fig.add_trace(go.Pie(
        labels=label_inner, values=value_inner,
        hole=0.6, marker=dict(colors=color_inner),
        showlegend=False,
        domain=dict(x=[0, 1], y=[0, 1])
    ))
    # Outer ring
    fig.add_trace(go.Pie(
        labels=labels_outer, values=values_outer,
        hole=0.7, direction='clockwise', sort=True,
        marker=dict(colors=[tech_colors[label] for label in labels_outer]),
        textinfo='percent', textposition='inside', showlegend=True,
        domain=dict(x=[0, 1], y=[0, 1])
    ))
    fig.update_layout(
        title_text="Installed Capacity ("+model+"). "+year0+" Inner - "+yearf+" Outer",
        height=9*50, width=16*50, template='plotly_white',
        margin=dict(t=100, b=50, l=50, r=50)
    )
    fig.write_image(f"{img_path}/scenarios/{scenario}/Installed Capacity {model}.png")
    fig.show()