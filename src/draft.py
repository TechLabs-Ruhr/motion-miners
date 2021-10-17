import seaborn as sns
import os

import defined_side_functions as sf


# ----------------------------------Userinput--------------------------------------------#

# change the path to where you stored tracerdata, and layoutfile on your computer
layout_path = r"layout.json"
tracer_folder_path = r""
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
    print("\n------------\n")
    print("Analysing tracer: ", filename)

    tracer, time = sf.extract_rssi_to_df(tracer_path)
    print("\n------------\n")
    print("\nTracer data:\n\n", tracer)

    merged_time_tracer = sf.merge_timeline(tracer)
    print("\n------------\n")
    print("\nMerged timeline data:\n\n", merged_time_tracer)

    located_tracer = sf.determine_flow_based_on_n_max_signal(merged_time_tracer, beacon_flow, 1)
    print("\n------------\n")
    print("\nFiltered tracer with flow:\n\n", located_tracer)

    person_dict_list, timelist = sf.time_analyse(located_tracer, time)
    print("\n------------\n")
    print("\nTotall Region times for Persons:\n\n", *person_dict_list, sep="\n")

    sf.plot_time_analyse(person_dict_list, filename, time, timelist)
