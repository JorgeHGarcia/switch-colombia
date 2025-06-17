def get():
    parse_tech = {'Eolica': 'Wind', 'Thermal': 'Thermal', 'pv_solar': 'Solar', 'Hidro': 'Hydro', 'RunOfRiver': 'Run of River'}
    colors = ['#3292A9','#C53707', '#55733D', '#F7AB17', '#808080', '#A6375F', '#8A8C46', '#73160E']
    tech_order = ["Hydro", "Thermal", "Solar", "Wind", "Run of River"]
    tech_colors = {
        'Hydro': colors[0], 'Thermal': colors[1],
        'Wind': colors[2], 'Solar': colors[3],
        'Run of River': colors[4], 'Minors':colors[5],
        'Biomass':colors[6],  'Geothermal':colors[7]
    }
    return parse_tech, colors, tech_order, tech_colors