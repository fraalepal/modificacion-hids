import plotly.graph_objects as go
import datetime
y = [1, 2, 3, 4, 5]
x = ["A", "B", "C", "D", "E"]
layout_title = "Evolución de la integridad de los archivos fecha:  " + \
    str(datetime.datetime.now().strftime("%d-%m-%Y"))
fig = go.Figure(
    data=[go.Bar(y=y, x=x)],
    layout_title_text=layout_title
)
fig.show()
