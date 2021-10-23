import os
import numpy as np

import seaborn as sns
from matplotlib import pyplot as plt

import waiting_side_functions as sf


# ----------------------------------Userinput-------------------------------------------#

# change the path to where you stored tracerdata, and layoutfile on your computer
layout_path = r"C:\Users\RR\Documents\TechLabs\100_final_Code_Folder\motion-miners\data\layout.json"
tracer_folder_path = (
    r"C:\Users\RR\Documents\TechLabs\100_final_Code_Folder\motionminer_testdata_temp"
)
# ---------------------------------------------------------------------------------------#


# ----------------------------------initial Values---------------------------------------#

Timeplate = np.zeros(shape=(9, 13))
person_counter = 0
pers_timesection_counter = [0] * 13
second_shot_tracers = []
# ---------------------------------------------------------------------------------------#


# ----------------------------------maincode---------------------------------------------#
layout = sf.create_mapped_layout(layout_path)
# print("\n------------\n")
# print(
#     "\nLayout:\n\n",
#     layout.loc[
#         :, ["beacon_id", "flow_id", "flow_beacon", "region_id", "region_beacon"]
#     ],
# )

beacon_flow = sf.get_flow_of_beacon(layout)
# print("\n------------\n")
# print("\nBeacon vs Flow:\n\n", beacon_flow)


# loop over the files in the tracer_folder_path
for filename in os.listdir(tracer_folder_path):
    tracer_path = os.path.join(tracer_folder_path, filename)
    # print("\n------------\n")
    # print("Analysing tracer: ", filename)

    tracer, time = sf.extract_rssi_to_df(tracer_path)
    # print("\n------------\n")
    # print("\nTracer data:\n\n", tracer)

    flow_tracer = sf.add_flow_as_multi_index(tracer, beacon_flow)
    # print("\n------------\n")
    # print("\nMulti index tracer data:\n\n",flow_tracer)

    max_signal_df = sf.get_max_signal_values(flow_tracer)
    # print("\n------------\n")
    # print("\nFiltered tracer data:\n\n",max_signal_df)

    person_dict_list, timelist = sf.time_analyse(max_signal_df, time)
    # print("\n------------\n")
    # print("\nTotall Region times for Persons:\n\n",*person_dict_list,sep="\n")

    region_times = sf.extract_time_spent_in_region(person_dict_list)

    if sf.is_second_shot(region_times, [3], [5]):
        second_shot_tracers.append(filename)

    person_counter, pers_timesection_counter, Timeplate = sf.timeplate_filler(
        person_dict_list, person_counter, pers_timesection_counter, Timeplate
    )

    sf.plot_time_analyse(region_times, filename, time, timelist)


print("\n------------\n")
print("\nTracers for second shot\n\n", second_shot_tracers)

print("\n------------\n")
print("\nNumber of person that are analysed:\n\n", person_counter)

print("\n------------\n")
print("\nNumber of Person for every timesection:\n\n", pers_timesection_counter)

sf.piechart(Timeplate)

np.savetxt("allTimeplate.csv", Timeplate, delimiter=";", fmt="%1.2f")

# ---------------------------------------------------------------------------------------#


# -----------------------------------additional------------------------------------------#

# plot the subdataframe from a person
# sns.relplot(
#     data=max_signal_df,
#     x="time",
#     y="location_of_tracer",
#     kind="line",
#     height=10,
# )
# plt.show()

# ---------------------------------------------------------------------------------------#
