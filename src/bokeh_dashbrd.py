# imports for bokeh
import pandas as pd
import numpy as np

from bokeh.io import show, curdoc
from bokeh.plotting import figure, output_file
from bokeh.layouts import row, column
from bokeh.models import Select
from bokeh.themes import built_in_themes

# from bokeh.resources import INLINE
from bokeh.models.widgets import Div, Panel, Tabs

# imports for analysis
import defined_side_functions as sf
import pickle

# theme
output_file("dark_minimal.html")
curdoc().theme = "dark_minimal"

# datafiles
layout_path = r"layout.json"
tracer_path = r"data\MMTS_00125_1620884397918.bin_beacon_data.pickle"
# --------------------------------------------------------------------------

# ------------------------required data------------------------------

layout = sf.create_mapped_layout(layout_path)
# print(
#     "\nLayout:\n\n",
#     layout.loc[
#         :, ["beacon_id", "flow_id", "flow_beacon", "region_id", "region_beacon"]
#     ],
# )

beacon_flow = sf.get_flow_of_beacon(layout)
# print("\n------------\n")
# print("\nBeacon vs Flow:\n\n", beacon_flow)

tracer, time = sf.extract_rssi_to_df(tracer_path)
# print("\n------------\n")
# print("\nTracer data:\n\n", tracer)

flow_tracer = sf.add_flow_as_multi_index(tracer, beacon_flow)
# print("\n------------\n")
# print("\nmulti_index Tracer data:\n\n",flow_tracer)

max_signal_df = sf.get_max_signal_values(flow_tracer)
# print("\n------------\n")
# print("\nfiltered tracer data:\n\n",max_signal_df)

person_dict_list, timelist = sf.time_analyse(max_signal_df, time)
# ----------------------------------------------------------------------

# -------------------------Add timestamps to dfs------------------------
# @TODO move to defined_side_functions

##Add timestamps to tracer_df and max_signal_df
timestamps_series = pd.Series(pd.date_range(time, periods=len(tracer), freq="0.1S"))

time_tracer = tracer.copy()
time_tracer = time_tracer.assign(time=timestamps_series.values)

time_max_value = max_signal_df.copy()
time_max_value = time_max_value.assign(time=timestamps_series.values)

# ----------------------------------------------------------------------

# ---------------------------Bokeh linechart----------------------------
line_chart = figure(
    plot_width=1000,
    plot_height=400,
    x_axis_type="datetime",
    title="Tracer route during %s" % str(time)[0:10],
)

line_chart.line(
    x="time",
    y="location_of_tracer",
    line_width=0.5,
    line_color="dodgerblue",
    legend_label="route",
    source=time_max_value,
)

line_chart.xaxis.axis_label = "Time"
line_chart.yaxis.axis_label = "Region"

line_chart.legend.location = "top_left"
# ----------------------------------------------------------------------

# ------------------part from plot_time_analysis_function---------------
region1_times = []
region3_times = []
region5_times = []
region6_times = []
region8_times = []

for person in person_dict_list:
    for key in person:
        if key == 1:
            region1_times.append(person[key])
        elif key == 3:
            region3_times.append(person[key])
        elif key == 5:
            region5_times.append(person[key])
        elif key == 6:
            region6_times.append(person[key])
        elif key == 8:
            region8_times.append(person[key])
        else:
            print(
                "Error, something went wrong!\n",
                "Check Line sidefunction , time_analyse",
            )

region_times_df = pd.DataFrame(
    list(
        zip(region1_times, region3_times, region5_times, region6_times, region8_times)
    ),
    columns=["region_1", "region_3", "region_5", "region_6", "region_8"],
)

# --------------------------Bokeh bar chart (one region)---------------------
bar_chart = figure(
    plot_width=500,
    plot_height=400,
    title="Time in minutes that persons spent in region 1",
)

bar_chart.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region_1"],
    fill_color="tomato",
    line_color="tomato",
    alpha=0.9,
)

bar_chart.xaxis.axis_label = "indivual person"
bar_chart.yaxis.axis_label = "time in minutes"

bar_chart.xaxis.ticker = [1, 2, 3, 4, 5, 6]
bar_chart.xaxis.major_label_overrides = {
    1: "Person 1",
    2: "Person 2",
    3: "Person 3",
    4: "Person 4",
    5: "Person 5",
    6: "Person 6",
}
# ------------------------------------------------------------------------------

# ---------------------------------All bar charts in tabs----------------------------
reg1 = figure(plot_width=500, plot_height=400,)
reg1.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region_1"],
    fill_color="tomato",
    line_color="tomato",
    alpha=0.9,
)
tab1 = Panel(child=reg1, title="region 1")

reg3 = figure(plot_width=500, plot_height=400,)
reg3.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region_3"],
    fill_color="gold",
    line_color="gold",
    alpha=0.9,
)
tab2 = Panel(child=reg3, title="region 3")

reg5 = figure(plot_width=500, plot_height=400,)
reg5.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region_5"],
    fill_color="slateblue",
    line_color="slateblue",
    alpha=0.9,
)
tab3 = Panel(child=reg5, title="region 5")

reg6 = figure(plot_width=500, plot_height=400,)
reg6.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region_6"],
    fill_color="forestgreen",
    line_color="forestgreen",
    alpha=0.9,
)
tab4 = Panel(child=reg6, title="region 6")

reg8 = figure(plot_width=500, plot_height=400,)
reg8.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region_8"],
    fill_color="darkturquoise",
    line_color="darkturquoise",
    alpha=0.9,
)
tab5 = Panel(child=reg8, title="region 8")

tabs = Tabs(tabs=[tab1, tab2, tab3, tab4, tab5])
# ------------------------------------------------------------------------------

# -----------------------Stacked bar chart--------------------------------------

num_ppl_str = ["1", "2", "3", "4", "5", "6"]
num_people = list(range(1, len(region1_times) + 1))
regions = ["region_1", "region_3", "region_5", "region_6", "region_8"]

region_time_dict = {
    "persons": num_ppl_str,
    "region_1": region1_times,
    "region_3": region3_times,
    "region_5": region5_times,
    "region_6": region6_times,
    "region_8": region8_times,
}

# print(region_time_dict)

cols = ["tomato", "gold", "slateblue", "forestgreen", "darkturquoise"]

stacked_bar = figure(
    x_range=num_ppl_str,
    title="Time in minutes for the vaccination process",
    plot_width=500,
    plot_height=450,
)
stacked_bar.vbar_stack(
    regions,
    x="persons",
    source=region_time_dict,
    color=cols,
    width=0.5,
    legend_label=regions,
)
# ------------------------------------------------------------------------------

# ----------------------------------Text element--------------------------------
expl = Div(
    text="""<b>Description</b> <br> 
    Region 1: Pre-checkin <br>
    Region 3: Checkin main <br>
    Region 5: Doctor table <br>
    Region 6: Vaccination <br>
    Region 8: Checkout <br>
    """,
    width=500,
    height=100,
)

# -----------------------------Combine to dashboard-----------------------------
title = Div(text='<h1 style="text-align: center">Demo dashboard</h1>')

# layout_dash = column(title, line_chart, row(bar_chart, tabs))
layout_dash = column(title, line_chart, row(tabs, stacked_bar), expl)

show(layout_dash)

# curdoc().title = "Project Dashboard"
# curdoc().add_root(layout_dash)
# ------------------------------------------------------------------------------

