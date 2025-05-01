def get():
    parse_tech = {'Eolica': 'Wind', 'Thermal': 'Thermal', 'pv_solar': 'Solar', 'Hidro': 'Hydro', 'RunOfRiver': 'Run of River'}
    colors = ['#3292A9','#C53707', '#55733D', '#F7AB17', '#808080']
    tech_order = ["Hydro", "Thermal", "Solar", "Wind", "Run of River"]
    tech_colors = {
        'Hydro': colors[0], 'Thermal': colors[1],
        'Wind': colors[2], 'Solar': colors[3],
        'Run of River': colors[4]
    }
    return parse_tech, colors, tech_order, tech_colors