import os
try:
    if os.getenv("SWCOL_SKIP_CHROME") != "1":
        import plotly.io as pio
        pio.get_chrome()
except Exception:
    pass
