import seaborn as sns
import os

import waiting_side_functions as sf


# ----------------------------------Userinput--------------------------------------------#

# change the path to where you stored tracerdata, and layoutfile on your computer
layout_path = r"layout.json"
# tracer_folder_path = r"C:\Users\RR\Documents\TechLabs\6_Motion_Miner\2_Code\2_Data"
tracer_folder_path = r"data"
# tracer_folder_path = r"C:\Users\RR\Desktop\Neuer Ordner (3)"
# ---------------------------------------------------------------------------------------#

# ----------------------------------maincode---------------------------------------------#

# loop over the files in the tracer_folder_path
for filename in os.listdir(tracer_folder_path):
    tracer_path = os.path.join(tracer_folder_path, filename)
    # print("\n------------\n")
    # print("Analysing tracer: ", filename)
    # print("\n------------\n")

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
    # print("\n------------\n")
    # print("\nTotall Region times for Persons:\n\n",*person_dict_list,sep="\n")

    ###plot_time_analyse not working yet?
    #sf.plot_time_analyse(person_dict_list, filename, time, timelist)

# ---------------------------------------------------------------------------------------


# -----------------------------------additional------------------------------------------#

# plot the subdataframe from a person
# sns.relplot(
#     data=subdataframe[1],
#     x=max_signal_df.time,
#     y="location_of_tracer",
#     kind="line",
#     height=10,
# )
# plt.show()

# ---------------------------------------------------------------------------------------#
