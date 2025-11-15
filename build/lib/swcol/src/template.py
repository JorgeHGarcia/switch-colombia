def get():
    parse_tech = {'Eolica': 'Wind', 'Thermal': 'Thermal', 'pv_solar': 'Solar', 'Hidro': 'Hydro', 'RunOfRiver': 'Run of River'}
    colors = ['#3292A9','#C53707', '#55733D', '#F7AB17', '#808080', '#A6375F', '#8A8C46', '#73160E', '#496373','#1B4159']
    tech_order = ["Hydro", "Run of River", "Thermal", "Solar", "Wind"]
    tech_colors = {
        'Hydro': colors[0], 'Thermal': colors[1],
        'Wind': colors[2], 'Solar': colors[3],
        'Run of River': colors[4], 'Minors':colors[5],
        'Biomass':colors[6],  'Geothermal':colors[7],
        'Biogas':colors[8], 'PCH':colors[9]
    }
    return parse_tech, colors, tech_order, tech_colors