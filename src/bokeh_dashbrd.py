import pandas as pd
import numpy as np

# imports for bokeh
from bokeh.io import show, curdoc
from bokeh.plotting import figure, output_file
from bokeh.layouts import row, column
from bokeh.models import Select, ColumnDataSource, LabelSet
from bokeh.themes import built_in_themes
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

# ---------------NEW
tracer_timestamps, max_timestamps = sf.add_timestamps_column(
    tracer, max_signal_df, time
)
region_times_df = sf.get_indvl_region_times(person_dict_list)
# ----------------------------------------------------------------------

# ---------------------------Bokeh linechart----------------------------
line_chart = figure(
    plot_width=1000,
    plot_height=400,
    x_axis_type="datetime",
    title="Tracer route during %s" % str(time)[0:10],
)

line_chart.line(
    x="timestamp",
    y="location_of_tracer",
    line_width=0.5,
    line_color="dodgerblue",
    legend_label="route",
    source=max_timestamps,
)

line_chart.xaxis.axis_label = "Time"
line_chart.yaxis.axis_label = "Region"

line_chart.legend.location = "top_left"
# ----------------------------------------------------------------------


# ---------------------------------All bar charts in tabs----------------------------
new_region_times_df = region_times_df.copy()
new_region_times_df["num_people"] = list(
    range(1, len(region_times_df["region1_times"]) + 1)
)
new_source = ColumnDataSource(round(new_region_times_df, 2))

reg1 = figure(plot_width=500, plot_height=420,)
reg1.yaxis.axis_label = "time in minutes"
reg1.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region1_times"],
    fill_color="tomato",
    line_color="tomato",
    alpha=0.9,
)
label1 = LabelSet(
    x="num_people",
    y="region1_times",
    text="region1_times",
    x_offset=0,
    y_offset=-20,
    text_font_size="15px",
    text_color="black",
    source=new_source,
    text_align="center",
    level="glyph",
    render_mode="canvas",
)
reg1.add_layout(label1)

tab1 = Panel(child=reg1, title="Region 1")


reg3 = figure(plot_width=500, plot_height=420,)
reg3.yaxis.axis_label = "time in minutes"
reg3.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region3_times"],
    fill_color="gold",
    line_color="gold",
    alpha=0.9,
)
label3 = LabelSet(
    x="num_people",
    y="region3_times",
    text="region3_times",
    x_offset=0,
    y_offset=-20,
    text_font_size="15px",
    text_color="black",
    source=new_source,
    text_align="center",
    level="glyph",
    render_mode="canvas",
)
reg3.add_layout(label3)

tab2 = Panel(child=reg3, title="Region 3")


reg5 = figure(plot_width=500, plot_height=420,)
reg5.yaxis.axis_label = "time in minutes"
reg5.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region5_times"],
    fill_color="slateblue",
    line_color="slateblue",
    alpha=0.9,
)
label5 = LabelSet(
    x="num_people",
    y="region5_times",
    text="region5_times",
    x_offset=0,
    y_offset=-20,
    text_font_size="15px",
    text_color="black",
    source=new_source,
    text_align="center",
    level="glyph",
    render_mode="canvas",
)
reg5.add_layout(label5)

tab3 = Panel(child=reg5, title="Region 5")


reg6 = figure(plot_width=500, plot_height=420,)
reg6.yaxis.axis_label = "time in minutes"
reg6.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region6_times"],
    fill_color="forestgreen",
    line_color="forestgreen",
    alpha=0.9,
)
label6 = LabelSet(
    x="num_people",
    y="region6_times",
    text="region6_times",
    x_offset=0,
    y_offset=-20,
    text_font_size="15px",
    text_color="black",
    source=new_source,
    text_align="center",
    level="glyph",
    render_mode="canvas",
)
reg6.add_layout(label6)

tab4 = Panel(child=reg6, title="Region 6")


reg8 = figure(plot_width=500, plot_height=420,)
reg8.yaxis.axis_label = "time in minutes"
reg8.vbar(
    x=[1, 2, 3, 4, 5, 6],
    width=0.9,
    top=region_times_df["region8_times"],
    fill_color="darkturquoise",
    line_color="darkturquoise",
    alpha=0.9,
)
label8 = LabelSet(
    x="num_people",
    y="region8_times",
    text="region8_times",
    x_offset=0,
    y_offset=-20,
    text_font_size="15px",
    text_color="black",
    source=new_source,
    text_align="center",
    level="glyph",
    render_mode="canvas",
)
reg8.add_layout(label8)

tab5 = Panel(child=reg8, title="Region 8")

tabs = Tabs(tabs=[tab1, tab2, tab3, tab4, tab5])
# ------------------------------------------------------------------------------

# -----------------------Stacked bar chart--------------------------------------

num_ppl_str = list(map(str, range(1, len(region_times_df["region1_times"]) + 1)))
num_people = list(range(1, len(region_times_df["region1_times"]) + 1))
regions = [
    "region_1",
    "region_3",
    "region_5",
    "region_6",
    "region_8",
]

region_time_dict = {
    "persons": num_ppl_str,
    "region_1": region_times_df["region1_times"],
    "region_3": region_times_df["region3_times"],
    "region_5": region_times_df["region5_times"],
    "region_6": region_times_df["region6_times"],
    "region_8": region_times_df["region8_times"],
}

cols = ["tomato", "gold", "slateblue", "forestgreen", "darkturquoise"]

stacked_bar = figure(
    x_range=num_ppl_str,
    title="Amount of time for the vaccination process",
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
stacked_bar.xaxis.axis_label = "person"
stacked_bar.yaxis.axis_label = "time in minutes"
# ------------------------------------------------------------------------------


# ----------------------------------Drop bar-----------------------------------
# example
drop_bar = Select(
    title="Dimension",
    options=[("1st vaccination"), ("2nd vaccination")],
    value="1st vaccination",
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

addition = Div(
    text="""<b>Key facts</b> <br> 
    Throughput time: ... <br>
    Waiting time for each region: ... <br>
    First vaccination: .... <br>
    Second vaccination: .... <br>
    <I> In a table? </I> <br>
    <I> Add map of vaccination center? </I>
    """,
    width=500,
    height=100,
)

# -----------------------------Combine to dashboard-----------------------------
title = Div(text='<h1 style="text-align: center">Demo dashboard</h1>')

# layout_dash = column(title, line_chart, row(bar_chart, tabs))
layout_dash = column(
    title, row(expl, addition), drop_bar, line_chart, row(stacked_bar, tabs)
)

show(layout_dash)

# curdoc().title = "Project Dashboard"
# curdoc().add_root(layout_dash)
# ------------------------------------------------------------------------------

