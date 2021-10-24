import pandas as pd
import numpy as np
import json
import pickle
import seaborn as sns
import datetime
import math
from matplotlib import pyplot as plt

import constant

""""
This py document contains all side functions that are used in main.py
"""


def create_mapped_layout(layout_path):
    """
    Create a completed layout has beacons, regions and flows
    Parameters
    ----------
    layout_path: str
        path of layout file
    Returns
    -------
    pandas.DataFrame
        a dataframe of beacons, regions and flows
    """
    with open(layout_path, "r") as layout_file:
        layout = json.load(layout_file)
        beacons_layout = pd.DataFrame.from_dict(layout["beacons"])
        regions_layout = pd.DataFrame.from_dict(layout["regions"])

    beacons_regions_layout = beacons_layout.merge(
        regions_layout, left_on="region_uuid", right_on="uuid"
    )

    beacons_regions_layout.rename(
        columns={
            "id_x": "beacon_id",
            "id_y": "region_id",
            "name": "region_name",
            "position_x": "b_pos_x",
            "position_y": "b_pos_y",
            "position_top_left_x": "rpos_top_left_x",
            "position_top_left_y": "rpos_top_left_y",
            "position_bottom_right_x": "rpos_bottom_right_x",
            "position_bottom_right_y": "rpos_bottom_right_y",
        },
        inplace=True,
    )
    beacons_regions_layout["region_beacon"] = (
        beacons_regions_layout["region_id"].astype(str)
        + "_"
        + beacons_regions_layout["beacon_id"].astype(str)
    )

    region_flow_df = pd.DataFrame.from_dict(data=constant.region_flow_dict)
    exploded_region_flow_df = region_flow_df.explode("region_id")

    final_layout = beacons_regions_layout.merge(
        exploded_region_flow_df, left_on="region_id", right_on="region_id"
    )
    final_layout["flow_beacon"] = (
        final_layout["flow_id"].astype(str)
        + "_"
        + final_layout["beacon_id"].astype(str)
    )

    return final_layout


def get_flow_of_beacon(layout):
    """
    Determine the flow id which beacon belongs to
    Parameters
    ----------
    layout: pandas.DataFrame
        the layout has mapped beacons, regions and flows
    Returns
    -------
    pandas.DataFrame
        a dataframe of beacons and its corresponding flow id
    """
    beacons_with_flow = layout.loc[
        :, ["beacon_id", "flow_id"]
    ]  # only the beacon and flow region ids are relevant here
    beacons_with_flow.sort_values(by=["flow_id", "beacon_id"], inplace=True)
    beacons_with_flow = beacons_with_flow[
        ["flow_id", "beacon_id"]
    ]  # change order of the columns

    return beacons_with_flow


def signal_to_m_converter(dataframe, dbm="4(dBm)"):
    """
    This function convert a (beacon)dataframe with signal values from the tracer
    to the corresponding *m*eter values, depend on dBm power that was used.
    By default dbm = 4(dBm)
    """
    # extract all different values from dataframe
    dataframe_unique_values = np.unique(dataframe)
    df_txpower = pd.DataFrame(constant.txpower_vs_distance)

    # extract the used power values from table_"Beacon_datasheet"
    choose_power = df_txpower[dbm]
    # caculate the lenght from powerlevel used for later iteration
    lenght_power = (df_txpower[dbm]).count()

    # empty list for collecting the corresponding meter values for each signal value
    list_meter_values = []
    flag = True
    # loop over unique_values over dataframe
    for value in dataframe_unique_values:
        # interpolation function
        for i in range(0, lenght_power):
            if choose_power[i] >= value and value >= choose_power[i + 1]:
                meter_value = (
                    (df_txpower["Distance(m)"][i + 1] - df_txpower["Distance(m)"][i])
                    / (choose_power[i + 1] - choose_power[i])
                    * (value - choose_power[i])
                    + df_txpower["Distance(m)"][i]
                )
                list_meter_values.append(meter_value)

                if flag:
                    print("\nDistance i+1", df_txpower["Distance(m)"][i + 1])
                    print("\nDistance i", df_txpower["Distance(m)"][i])
                    print("\nchoose_power i+1", choose_power[i + 1])
                    print("\nchoose_power i", choose_power[i])
                    print("\nvalue", value)
                    print("\ndf_txpower[distance][i]", df_txpower["Distance(m)"][i])
                    flag = False
                break
        else:
            meter_value = np.nan
            list_meter_values.append(meter_value)

    mod_dataframe = dataframe.replace(list(dataframe_unique_values), list_meter_values)
    return mod_dataframe


def extract_rssi_to_df(tracer_data_path):
    """
    Takes path from pickle file and create a df with a timeline and the rssi_arr values
    Parameters
    ----------
    tracer_data_path: str
        path to tracer data file
    Returns
    -------
    pandas.DataFrame
        tracer data
    """
    # create a dataframe df from the picke.file
    df_file = pickle.load(open(tracer_data_path, "rb"))

    # extract rssi_arr key to numpy.array
    rssi_arr = df_file["rssi_arr"]

    # extract the time stamp
    timestamp = df_file["timestamp"]

    # set -inf equal to 0 (datacleaning)
    rssi_arr[rssi_arr == -np.Inf] = np.nan

    # figure out the shape from rssi_arr array for the timeline
    dim = np.shape(rssi_arr)

    # create a timeline and add it to the rssi_arr array
    # problem that it changes from 0091 file to others why?
    timeline = np.linspace(0.1, (dim[0]) * 0.1, dim[0]).reshape(dim[0], 1)
    mod_rssi_arr = np.append(rssi_arr, timeline, axis=1)

    # create the colum_names for df_rssi_arr (dataframe)
    # Beacon 252 does not exist
    # colum_names = []
    # for i in range(1, dim[1] + 2):
    #     if i == 52:
    #         continue
    #     else:
    #         value = "Beacon_" + str(200 + i)
    #         colum_names.append(value)
    # colum_names.append("timeline[s]")

    # beacon id as column
    colum_names = df_file["beacon_uuids"]
    colum_names = np.append(colum_names, "timeline[s]")

    # create df_rssi_arr
    df_rssi_arr = pd.DataFrame(data=mod_rssi_arr, columns=colum_names)
    df = df_rssi_arr.set_index("timeline[s]")

    return df, timestamp


def add_flow_as_multi_index(tracer_df, beacon_flow):
    """
    Add flow id as second level column to tracer data
    Parameters
    ----------
    tracer_df: pandas.DataFrame
        tracer data
    beacon_flow: pandas.DataFrame
        the map of beacon and flow
    Returns
    -------
    pandas.DataFrame
        tracer data with multi column (multi index)
    """

    tracer_df.columns = tracer_df.columns.map(int)

    # list beacons that were not used
    not_used_beacons = []
    other_not_used_beacons = []
    for beacon in tracer_df.columns.values:
        if beacon not in list(beacon_flow["beacon_id"]):
            not_used_beacons.append(beacon)

    for index, row_beacon in beacon_flow.iterrows():
        if row_beacon["beacon_id"] not in list(tracer_df.columns.values):
            other_not_used_beacons.append(row_beacon["beacon_id"])

    # delete beacon_columns that were not used (in both dfs)
    new_tracer_df = tracer_df.drop(not_used_beacons, axis=1)
    beacon_flow = beacon_flow.drop(
        beacon_flow[beacon_flow.beacon_id.isin(other_not_used_beacons)].index, axis=0
    )

    # get tuples of flow + beacon in order to use pd.MultiIndex.from_tuples
    multi_col_flow_tuple = list(beacon_flow.to_records(index=False))
    multi_col_flow_tuple.sort(key=lambda tup: tup[1])  # sort the tuple by beacon ids

    # add multicolumn index
    new_tracer_df.columns = pd.MultiIndex.from_tuples(
        multi_col_flow_tuple, names=("Flow", "Beacon")
    )

    return new_tracer_df[np.sort(new_tracer_df.columns)]


def get_max_signal_values(tracer_df):
    max_df = pd.DataFrame(
        data=list(tracer_df.max(axis=1)),
        index=range(len(tracer_df)),
        columns=["max_signal"],
    )  # max values of each row in the original df
    max_df["time"] = tracer_df.index
    max_df["region_beacon"] = list(
        tracer_df.idxmax(axis=1)
    )  # corresponding beacon id and region number of the max value

    # max_signal = max(max_df["max_signal"]) - 30
    # mean_signal = np.mean(max_df["max_signal"]) + 10

    location = []
    for row in max_df.itertuples():
        current_high = row[3]
        if len(location) == 0:
            location.append(0)
        elif row[1] >= -65:
            location.append(row[3][0])
        else:
            if location[-1] == 1:
                location.append(2)
            elif location[-1] == 3:
                location.append(4)
            elif location[-1] == 6:
                location.append(7)
            elif location[-1] == 8:
                location.append(9)
            else:
                location.append(location[-1])

    max_df["location_of_tracer"] = location

    max_df = max_df[["time", "max_signal", "region_beacon", "location_of_tracer"]]

    return max_df


# def get_min_distance_values(tracer_df):
#     min_df = pd.DataFrame(
#         data=list(tracer_df.min(axis=1)),
#         index=range(len(tracer_df)),
#         columns=["min_distance"],
#     )  # min values of each row in the original df
#     min_df["time"] = tracer_df.index
#     # corresponding beacon id and region number of the max value
#     min_df["region_beacon"] = list(tracer_df.idxmin(axis=1))
#     # max_df['location_of_tracer'] = 0 #zero as default

#     location = []
#     for row in min_df.itertuples():
#         # if the maximum value is under -65 (adjust the value?) then the tracer is located in the respoing region
#         if row[1] < -65:
#             location.append(row[3][0])
#         # otherwise the tracer can be still allocated to the previous region (the region where it has been located before)
#         else:
#             location.append(location[-1])

#     min_df["location_of_tracer"] = location
#     min_df = min_df[["time", "min_distance", "region_beacon", "location_of_tracer"]]
#     min_df["location_number"] = min_df["location_of_tracer"].replace(
#         constant.regions, range(0, 10)
#     )

#     return min_df


def order_list(df_location):
    order_reg = []
    order_reg_index = []

    for index, value in df_location.iteritems():
        if index == 0:
            order_reg.append(value)
            order_reg_index.append([value, index])
        elif value != order_reg_index[-1][0]:
            order_reg.append(value)
            order_reg_index.append([value, index])
    return order_reg, order_reg_index


def make_person_list(order_of_df, o_plus_index):
    newlist = []
    innerlist = []

    for index, value in enumerate(order_of_df):
        if index == 0 and value == 0:
            next
        elif value != 0:
            innerlist.append(value)
        else:
            newlist.append(value)
            newlist.append(innerlist)
            innerlist = []

    newlist_tup = []
    innerlist_tup = []

    for index, values in enumerate(o_plus_index):
        if index == 0 and values[0] == 0:
            next
        elif values[0] != 0:
            innerlist_tup.append((values[0], values[1]))
        else:
            newlist_tup.append((values[0], values[1]))
            newlist_tup.append(innerlist)
            innerlist_tup = []

    return newlist, newlist_tup


def plot_beacon(beacon, dataframe):
    """
    This plot function plots the values from a beacon over the time.
    Input beacon as a string format -> beacon= "Beacon_2xx" .
    """
    sns.relplot(x="timeline[s]", y=beacon, data=dataframe, kind="scatter")
    plt.title(beacon)
    plt.xlabel("Time[s]")
    plt.ylabel("Distance person between Beacon[m]")
    plt.show()


def plot_region(region_as_number, dataframe):
    """
    This plot function plots the values from beacons in a section area as a scatter plot.
    Input section_as_number as a integer.
    """
    # extract index time and add it as a column
    df_mod_without_timelineindex = dataframe.reset_index()
    # from above (beginning py file) it takes the name of the section
    select_region = constant.regions[region_as_number]
    # from above (beginning py file) it takes the name of the beacons
    beacons_in_region = constant.beacons_each_region[select_region]
    # loop over the beacons in the section
    for beacon in beacons_in_region:
        plt.scatter(
            df_mod_without_timelineindex["timeline[s]"],
            df_mod_without_timelineindex[beacon],
            alpha=0.7,
            label=beacon,
        )
    plt.title(select_region)
    plt.xlabel("Time[s]")
    plt.ylabel("Distance person between Beacon[m]")
    plt.legend()
    plt.show()


def beacons_list_from_region(region_as_number):
    """
    This fuction gives you the associated beacons as a list in the section you want.
    """
    # from above (beginning py file) it takes the name of the section
    select_region = constant.regions[region_as_number]
    # from above (beginning py file) it takes the name of the beacons
    beacons_in_region = constant.beacons_each_region[select_region]
    return beacons_in_region


def number_to_region(region_number):
    region_name = constant.regions[region_number]
    return region_name


def region_to_number(value):
    region_name = int(constant.regions[value].index)
    return region_name


def time_analyse(max_signal_df, timestamp):

    ##Step 1)
    # sclicing max_signal_df into possible persons by separate zeros
    flag = True
    slicing_index = []
    for index, row in max_signal_df.iterrows():
        if flag == True:
            if row["location_of_tracer"] == 0:
                slicing_index.append(index)
                flag = False
        else:
            if row["location_of_tracer"] != 0:
                flag = True

    ##Step 2)
    # set a subdataframe for every possible person and filter the "real" person
    subdataframe = []
    person_df = []
    for i in range(len(slicing_index) - 1):
        subdataframe.append("sub_df_" + str(i))
        subdataframe[i] = max_signal_df.loc[
            slicing_index[i] : (slicing_index[i + 1] - 1)
        ]
        # filter the subdataframe to possible persons who enter the regions [0,1,3,5,6,8] + waiting
        if np.all(
            np.unique(subdataframe[i]["location_of_tracer"])
            == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
        ):
            person_df.append(i)
            # filter the zero region values out
            subdataframe[i] = subdataframe[i][subdataframe[i].location_of_tracer != 0]

    ##Step 3)
    # get the time values
    vacc_time = []
    person_dict_list = []
    persondaytime_list = []
    for person in person_df:
        # get the full times the person need for a vaccination
        time_min = (
            subdataframe[person]["time"].iloc[-1] - subdataframe[person]["time"].iloc[0]
        ) / 60
        vacc_time.append(time_min)
        persondaytime_begin = timestamp + datetime.timedelta(
            seconds=int(subdataframe[person]["time"].iloc[0])
        )
        persondaytime_end = timestamp + datetime.timedelta(
            seconds=int(subdataframe[person]["time"].iloc[-1])
        )
        persondaytime_list.append(
            persondaytime_begin.strftime("%H:%M:%S")
            + " -\n"
            + persondaytime_end.strftime("%H:%M:%S")
        )
        # calculate the time a person need for every region
        region = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        row = 0
        temp = []
        dic_times = {}
        while row < subdataframe[person].shape[0]:
            if subdataframe[person]["location_of_tracer"].iloc[row] in region:
                region_nr = subdataframe[person]["location_of_tracer"].iloc[row]
                while (
                    row < subdataframe[person].shape[0]
                    and subdataframe[person]["location_of_tracer"].iloc[row]
                    == region_nr
                ):
                    temp.append(subdataframe[person]["time"].iloc[row])
                    row = row + 1
                dic_times.setdefault(region_nr, []).append((temp[-1] - temp[0]) / 60)
                temp = []

        #add a time key to the dict 
        dic_times["time"]=[persondaytime_begin.strftime("%H:%M:%S"),persondaytime_end.strftime("%H:%M:%S")]
        person_dict_list.append(dic_times)

    ##Step 4)
    # filter the rush signals by sum up the region times to one representative value
    for person in person_dict_list:
        for key in person:
            if key =="time":
                continue
            else:
                person[key] = sum(person[key])

    return person_dict_list, persondaytime_list


def extract_time_spent_in_region(person_dict_list):
    """
    Get the time spent in each region
    Parameters
    ----------
    person_dict_list: list
        regions people have passed during vaccination lifecycle
    Returns
    -------
    dict
        time spent in each region
    """

    # seperate the time values for each region
    region1_times = []
    region2_times = []
    region3_times = []
    region4_times = []
    region5_times = []
    region6_times = []
    region7_times = []
    region8_times = []
    region9_times = []

    for person in person_dict_list:
        for key in person:
            if key == 1:
                region1_times.append(person[key])
            elif key == 2:
                region2_times.append(person[key])
            elif key == 3:
                region3_times.append(person[key])
            elif key == 4:
                region4_times.append(person[key])
            elif key == 5:
                region5_times.append(person[key])
            elif key == 6:
                region6_times.append(person[key])
            elif key == 7:
                region7_times.append(person[key])
            elif key == 8:
                region8_times.append(person[key])
            elif key == 9:
                region9_times.append(person[key])
            elif key =="time":
                continue                
            else:
                raise RuntimeError(
                    "There is region key different from [1, 3, 5, 6, 8] and waiting rooms. Unknown region %d",
                    key,
                )

    return {
        "region1": region1_times,
        "region2": region2_times,
        "region3": region3_times,
        "region4": region4_times,
        "region5": region5_times,
        "region6": region6_times,
        "region7": region7_times,
        "region8": region8_times,
        "region9": region9_times,
    }


def is_second_shot(region_times, regions, thresholds, require_all=False):
    """
    Check if tracer is used for 2nd vaccination
    Parameters
    ----------
    region_times: dict
        the time spent in each region
    regions: list
        the regions will be validated
    thresholds: list
        the amount of time (in minutes) in a region which is the limit for 2nd vaccination
    require_all: boolean
        whether all regions must under threshold or not
    Returns
    -------
    boolean
    """

    region_times_df = pd.DataFrame.from_dict(region_times)
    region_times_df.columns = [1, 2, 3, 4, 5, 6, 7, 8, 9]

    selected_regions = region_times_df.loc[:, regions]

    selected_regions_median = selected_regions.median(axis="index")

    compared = selected_regions_median < thresholds

    if require_all:
        return compared.all()
    else:
        return compared.any()


##### NOT WORKING AND REGION 9 IS MISSING
def plot_time_analyse(region_times, filename, timestamp, timelist):
    """
    Visualize time spent in each region
    Parameters
    ----------
    region_times: dict
        the time spent in each region
    filename: string
        the name of dataset which is processed
    timestamp: string
        the time that dataset started recording
    timelist
    Returns
    -------
    void
    """

    ##Step 1)
    region1_times = region_times["region1"]
    region2_times = region_times["region2"]
    region3_times = region_times["region3"]
    region4_times = region_times["region4"]
    region5_times = region_times["region5"]
    region6_times = region_times["region6"]
    region7_times = region_times["region7"]
    region8_times = region_times["region8"]
    region9_times = region_times["region9"]

    ##Step2)
    # making a stack bar plot
    labels = range(1, len(region1_times) + 1)
    width = 0.8
    fig, ax = plt.subplots()

    # setting the bars for the plot
    ax.bar(labels, region1_times, width, label="Pre-checkin")
    ax.bar(labels, region2_times, width, bottom=region1_times, label="Waiting Checkin")
    ax.bar(
        labels,
        region3_times,
        width,
        bottom=np.array(region1_times) + np.array(region2_times),
        label="Checkin main",
    )
    ax.bar(
        labels,
        region4_times,
        width,
        bottom=np.array(region1_times)
        + np.array(region2_times)
        + np.array(region3_times),
        label="Waiting I",
    )
    ax.bar(
        labels,
        region5_times,
        width,
        bottom=np.array(region1_times)
        + np.array(region2_times)
        + np.array(region3_times)
        + np.array(region4_times),
        label="Doctor table",
    )
    ax.bar(
        labels,
        region6_times,
        width,
        bottom=np.array(region1_times)
        + np.array(region2_times)
        + np.array(region3_times)
        + np.array(region4_times)
        + np.array(region5_times),
        label="Vaccination",
    )
    ax.bar(
        labels,
        region7_times,
        width,
        bottom=np.array(region1_times)
        + np.array(region2_times)
        + np.array(region3_times)
        + np.array(region4_times)
        + np.array(region5_times)
        + np.array(region6_times),
        label="Waiting II",
    )
    ax.bar(
        labels,
        region8_times,
        width,
        bottom=np.array(region1_times)
        + np.array(region2_times)
        + np.array(region3_times)
        + np.array(region4_times)
        + np.array(region5_times)
        + np.array(region6_times)
        + np.array(region7_times),
        label="Checkout",
    )
    ax.bar(
        labels,
        region9_times,
        width,
        bottom=np.array(region1_times)
        + np.array(region2_times)
        + np.array(region3_times)
        + np.array(region4_times)
        + np.array(region5_times)
        + np.array(region6_times)
        + np.array(region7_times)
        + np.array(region8_times),
        label="Waiting III",
    )  

    ax.set_ylabel("time[min]")
    ax.set_xlabel("persons")

    # title
    weekday_date = timestamp.strftime("%A,%d.%m.%Y")
    ax.set_title(weekday_date + "\n" + str(filename))

    # x-axis title , time from start to end of each person
    plt.xticks(range(1, len(region1_times) + 1), timelist)
    ax.legend()

    ##setting the time text in the plot
    # region1
    for index, value in enumerate(region1_times):
        plt.text(
            index + 1 - 0.2,
            value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )

    # region2
    for index, value in enumerate(region2_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )

    #region3
    for index, value in enumerate(region3_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )
    
    #region4
    for index, value in enumerate(region4_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )

    #region5
    for index, value in enumerate(region5_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + region4_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )
    
    #region6
    for index, value in enumerate(region6_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + region4_times[index]
            + region5_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )

    #region7
    for index, value in enumerate(region7_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + region4_times[index]
            + region5_times[index]
            + region6_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )

    #region8
    for index, value in enumerate(region8_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + region4_times[index]
            + region5_times[index]
            + region6_times[index]
            + region7_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )

    #region9
    for index, value in enumerate(region9_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + region4_times[index]
            + region5_times[index]
            + region6_times[index]
            + region7_times[index]
            + region8_times[index]
            + value / 2,
            str(round(value, 2)) + "min",
            color="k",
            fontweight="bold",
        )


    # fulltime
    for index, value in enumerate(region9_times):
        plt.text(
            index + 1 - 0.2,
            region1_times[index]
            + region2_times[index]
            + region3_times[index]
            + region4_times[index]
            + region5_times[index]
            + region6_times[index]
            + region7_times[index]
            + region8_times[index]
            + value
            + 1,
            str(
                round(
                    region1_times[index]
                    + region2_times[index]
                    + region3_times[index]
                    + region4_times[index]
                    + region5_times[index]
                    + region6_times[index]
                    + region7_times[index]
                    + region8_times[index]
                     + value,
                    2,
                )
            )
            + "min",
            color="k",
            fontweight="bold",
        )

    fig =plt.gcf()
    fig.set_size_inches(15,12)
    fig.savefig(filename.split(".")[0],dpi=300)
    # plt.show()


def merge_timeline(tracer_df):
    old_index_list = tracer_df.index.tolist()
    round_index_list = [math.floor(num) for num in old_index_list]
    new_tracer_df = tracer_df.copy()
    new_tracer_df.index = round_index_list
    new_tracer_df = new_tracer_df.groupby(level=0).mean()

    return new_tracer_df


def determine_flow_based_on_n_max_signal(tracer_df, beacon_flow, n_max_values=3):
    tracer_df.columns = tracer_df.columns.map(int)

    # delete beacon columns in tracer data that don't exist in flow map
    not_used_beacons = []
    for beacon in tracer_df.columns.values:
        if beacon not in list(beacon_flow["beacon_id"]):
            not_used_beacons.append(beacon)

    new_tracer_df = tracer_df.drop(not_used_beacons, axis=1)

    # delete beacon rows in beacon flow that don't exist in tracer data
    beacons_not_exist_in_data = []
    for index, row_beacon in beacon_flow.iterrows():
        if row_beacon["beacon_id"] not in list(tracer_df.columns.values):
            beacons_not_exist_in_data.append(row_beacon["beacon_id"])

    new_beacon_flow = beacon_flow.copy().drop(
        beacon_flow[beacon_flow.beacon_id.isin(beacons_not_exist_in_data)].index, axis=0
    )

    # alter column name of tracer data with flow_id instead of beacon_id
    beacon_flow_softed_by_beacon = new_beacon_flow.sort_values(by="beacon_id")
    new_tracer_df.columns = beacon_flow_softed_by_beacon["flow_id"]

    location_of_tracer = []
    for index, row in new_tracer_df.iterrows():
        flow_has_max_values = row.nlargest(n_max_values, "all")
        grouped_by_flow = flow_has_max_values.groupby(level=0).count()
        if grouped_by_flow.empty:
            if len(location_of_tracer) == 0:
                location_of_tracer.append(0)
            else:
                location_of_tracer.append(location_of_tracer[-1])
        else:
            flow_has_max_count = grouped_by_flow.idxmax()
            location_of_tracer.append(flow_has_max_count)

    new_df = pd.DataFrame()
    new_df["time"] = new_tracer_df.index
    new_df["location_of_tracer"] = location_of_tracer

    return new_df


def add_timestamps_column(tracer_df, max_signal_df, start_timestamp):
    # adds timestamps to dfs for dashboard charts

    timestamps_series = pd.Series(
        pd.date_range(start_timestamp, periods=len(tracer_df), freq="0.1S")
    )

    tracer_with_timestamp = tracer_df.copy()
    tracer_with_timestamp = tracer_with_timestamp.assign(
        timestamp=timestamps_series.values
    )

    max_with_timestamp = max_signal_df.copy()
    max_with_timestamp = max_with_timestamp.assign(timestamp=timestamps_series.values)

    return tracer_with_timestamp, max_with_timestamp


def add_single_timestamps_column(tracer_df, start_timestamp):
    # adds timestamps to dfs for dashboard charts

    timestamps_series = pd.Series(
        pd.date_range(start_timestamp, periods=len(tracer_df), freq="0.1S")
    )

    tracer_with_timestamp = tracer_df.copy()
    tracer_with_timestamp = tracer_with_timestamp.assign(
        timestamp=timestamps_series.values
    )

    return tracer_with_timestamp


def get_indvl_region_times(person_dict_list):

    region1_times = []
    region2_times = []
    region3_times = []
    region4_times = []
    region5_times = []
    region6_times = []
    region7_times = []
    region8_times = []
    region9_times = []

    for person in person_dict_list:
        for key in person:
            if key == 1:
                region1_times.append(person[key])
            elif key == 2:
                region2_times.append(person[key])
            elif key == 3:
                region3_times.append(person[key])
            elif key == 4:
                region4_times.append(person[key])
            elif key == 5:
                region5_times.append(person[key])
            elif key == 6:
                region6_times.append(person[key])
            elif key == 7:
                region7_times.append(person[key])
            elif key == 8:
                region8_times.append(person[key])
            elif key == 9:
                region9_times.append(person[key])
            elif key == "time":
                continue                
            else:
                raise RuntimeError(
                    "There is region key different from [1, 3, 5, 6, 8] and waiting rooms. Unknown region %d",
                    key,
                )

    region_time_df = pd.DataFrame(
        list(
            zip(
                region1_times,
                region2_times,
                region3_times,
                region4_times,
                region5_times,
                region6_times,
                region7_times,
                region8_times,
                region9_times,
            )
        ),
        columns=[
            "region1_times",
            "region2_times",
            "region3_times",
            "region4_times",
            "region5_times",
            "region6_times",
            "region7_times",
            "region8_times",
            "region9_times",
        ],
    )

    return region_time_df


def timeplate_binder(key,timesection,Timeplate,person):
    transfer_list= [0,0,1,2,3,4,5,6,7,8]
    Timeplate[transfer_list[key],timesection]=Timeplate[transfer_list[key],timesection] + person[key]
    return Timeplate


def timeplate_filler(person_dict_list,person_counter,pers_timesection_counter,Timeplate):
    for person in person_dict_list:

        if datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("08:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[0]=pers_timesection_counter[0]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,0,Timeplate,person)
                
        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("09:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("08:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[1]=pers_timesection_counter[1]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,1,Timeplate,person)
        
        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("10:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("09:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[2]=pers_timesection_counter[2]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,2,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("11:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("10:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[3]=pers_timesection_counter[3]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,3,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("12:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("11:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[4]=pers_timesection_counter[4]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,4,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("13:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("12:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[5]=pers_timesection_counter[5]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,5,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("14:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("13:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[6]=pers_timesection_counter[6]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,6,Timeplate,person)
        
        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("15:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("14:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[7]=pers_timesection_counter[7]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,7,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("16:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("15:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[8]=pers_timesection_counter[8]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,8,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("17:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("16:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[9]=pers_timesection_counter[9]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,9,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("18:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("17:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[10]=pers_timesection_counter[10]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,10,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") < datetime.datetime.strptime("19:00:00","%H:%M:%S") and datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("18:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[11]=pers_timesection_counter[11]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,11,Timeplate,person)

        elif datetime.datetime.strptime(person["time"][0],"%H:%M:%S") >= datetime.datetime.strptime("19:00:00","%H:%M:%S"):
            person_counter=person_counter+1
            pers_timesection_counter[12]=pers_timesection_counter[12]+1
            for key in person:
                if key == 1 or key == 3 or key == 5 or key == 6 or key == 8 or key == 2 or key == 4 or key == 7 or key == 9:
                    Timeplate=timeplate_binder(key,12,Timeplate,person)

    return person_counter,pers_timesection_counter,Timeplate


def piechart(Timeplate):
    labels = 'Pre-checkin', 'Waiting checking', 'Checkin main', 'Waiting I', 'Doctor table', 'Vaccination', 'Waiting II' ,"Checkout", 'Waiting III'
    sizes = np.sum(Timeplate,axis=1)
    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
    shadow=True, startangle=90)
    ax1.axis('equal')

    plt.savefig("Number of person that are analysed")

def csv_Timeplate_output(Timeplate,pers_timesection_counter,filename):
    Timeplate= np.vstack([Timeplate,pers_timesection_counter])

    Timeplate_columns=[
    "before 8",
    "8 to 9",
    "9 to 10",
    "10 to 11",
    "11 to 12",
    "12 to 13",
    "13 to 14",
    "14 to 15",
    "15 to 16",
    "16 to 17",
    "17 to 18",
    "18 to 19",
    "afer 19",
    ]

    Timeplate_rows=[
    "Region 1: Pre-checkin",
    "Region 2: Waiting Checkin",
    "Region 3: Checkin main",
    "Region 4: Waiting I",
    "Region 5: Doctor table",
    "Region 6: Vaccination",
    "Region 7: Waiting II",
    "Region 8: Checkout",
    "Region 9: Waiting III",
    "Person per section"
    ]
    Timeplate_df = pd.DataFrame(data=Timeplate, index= Timeplate_rows, columns= Timeplate_columns)
    Timeplate_df.to_csv (filename, index = True, header=True,sep=";",decimal=",")

