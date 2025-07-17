import pandas as pd

def rearr_datetime_cols(df):
    """ rearranging to have the columns in a more readable order """
    datetime_cols = ['PU_datetime', 'DO_datetime', 'duration_mins', 'trip_distance', 'passenger_count', 'PU_Zone', 'PU_service_zone', 'DO_Zone', 'DO_service_zone']
    df = df[datetime_cols + [c for c in df.columns if c not in datetime_cols]]
    return df

def remove_outliers(df, duration_col='duration_mins', distance_col='trip_distance', lower=0.01, upper=0.99):
    """
    remove rows with non-positive duration or distance, then filter out extreme outliers
    based on quantiles for both duration and distance columns.
    returns a cleaned DataFrame with index reset.
    """
    # remove negative values
    df_clean = df[(df[duration_col] > 0) & (df[distance_col] > 0)].copy()
    # calculate quantile thresholds
    duration_min = df_clean[duration_col].quantile(lower)
    duration_max = df_clean[duration_col].quantile(upper)
    distance_min = df_clean[distance_col].quantile(lower)
    distance_max = df_clean[distance_col].quantile(upper)
    # filter out outliers
    mask = (
        df_clean[duration_col].between(duration_min, duration_max) &
        df_clean[distance_col].between(distance_min, distance_max)
    )
    return df_clean[mask].reset_index(drop=True)

def same_zone_perc(borough, borough_overall, borough_name, PU='PU_Zone', DO='DO_Zone'):
    """returns % of rides within the same zone for rides strictly within and involving the borough"""
    # strictly within the borough
    percentage_within = (borough[borough[PU] == borough[DO]].shape[0] / borough.shape[0]) * 100
    print(f"% of same zone rides within {borough_name}: {percentage_within:.2f}%")

    # borough-involved rides
    percentage_involved = (borough[borough[PU] == borough[DO]].shape[0] / borough_overall.shape[0]) * 100
    print(f"% of same zone rides involving {borough_name}: {percentage_involved:.2f}%")

def identify_cancelled_rides(df, ride_id_cols = ['VendorID','PU_datetime', 'DO_datetime', 'PULocationID', 'DOLocationID', 'duration_mins', 'trip_distance', 'passenger_count', 'payment_type', 'RatecodeID']):
    """
    'ride_id_cols' serve as a unique ride identification, EXCEPT fare_amount since we want to match pairs of rides with opposite fare amounts
    remove rides with negative fare amounts, which are likely cancelled or refunded.
    returns a cleaned DataFrame with index reset.
    """
    # filters for negative and positive fare amounts
    neg_fare = df[df['fare_amount'] < 0].copy()
    pos_fare = df[df['fare_amount'] > 0].copy()

    # merge the dfs
    merged_fares = neg_fare.merge(pos_fare, on=ride_id_cols, suffixes=('_neg', '_pos'))
    
    # now we have all the pairs where fare amounts are exact opposites
    matched_pairs = merged_fares[merged_fares['fare_amount_neg'] == -merged_fares['fare_amount_pos']]

    return matched_pairs

def remove_cancelled_fare_pairs(df, matched_pairs, ride_id_cols = ['VendorID','PU_datetime', 'DO_datetime', 'PULocationID', 'DOLocationID', 'duration_mins', 'trip_distance', 'passenger_count', 'payment_type', 'RatecodeID']):
    """
    remove cancelled fare pairs from the original DataFrame using index-based removal.
    removes both sides of the matched pairs (negative and positive fares).
    """
    # Get the index of the matched pairs (from the merged DataFrame)
    matched_idx = matched_pairs.index
    # Remove rows from df whose index is in matched_idx
    df_cleaned = df[~df.index.isin(matched_idx)]
    # Remove any remaining negative fares not affiliated with a matching pair
    df_cleaned = df_cleaned[df_cleaned['fare_amount'] >= 0]
    return df_cleaned.reset_index(drop=True)

def categorize_zones(borough_pu, borough_do, borough_avg_fare, avg_fare_col='avg_fare', pu_zone_col='PU_Zone', do_zone_col='DO_Zone'):
    """
    categorize zones based on average fare amounts and their quartiles
    returns 3 dataframes: pricey_zones, cheap_zones, avg_zones
    - pricey_zones: zones with fares above the 75th percentile of borough average fare
    - cheap_zones: zones with fares below the 25th percentile of borough average fare
    - avg_zones: zones with fares between the 25th and 75th percentiles of borough average fare 
    """
    # finding the 75th percentile of fares that are above the borough average fare 
    pu_75 = borough_pu[borough_pu[avg_fare_col] > borough_avg_fare][avg_fare_col].quantile(0.75)
    do_75 = borough_do[borough_do[avg_fare_col] > borough_avg_fare][avg_fare_col].quantile(0.75)

    # finding the 25th percentile of fares that are lower than the borough average fare 
    pu_25 = borough_pu[borough_pu[avg_fare_col] < borough_avg_fare][avg_fare_col].quantile(0.25)
    do_25 = borough_do[borough_do[avg_fare_col] < borough_avg_fare][avg_fare_col].quantile(0.25)

    # pricier zones: based on the 75th percentile of fares
    pricey_pu_zones = borough_pu[(borough_pu[avg_fare_col] > borough_avg_fare) & (borough_pu[avg_fare_col] > pu_75)][pu_zone_col]  
    pricey_do_zones = borough_do[(borough_do[avg_fare_col] > borough_avg_fare) & (borough_do[avg_fare_col] > do_75)][do_zone_col]
    pricey_zones = pd.concat([pricey_pu_zones, pricey_do_zones], axis=0).drop_duplicates().reset_index(drop=True).to_frame(name='pricier_zones')

    # cheap zones: based on the 25th percentile of fares
    cheap_pu_zones = borough_pu[(borough_pu[avg_fare_col] < borough_avg_fare) & (borough_pu[avg_fare_col] < pu_25)][pu_zone_col]  
    cheap_do_zones = borough_do[(borough_do[avg_fare_col] < borough_avg_fare) & (borough_do[avg_fare_col] < do_25)][do_zone_col]
    cheap_zones = pd.concat([cheap_pu_zones, cheap_do_zones], axis=0).drop_duplicates().reset_index(drop=True).to_frame(name='cheaper_zones')

    # average zones: based on the 25th and 75th percentiles of fares
    avg_pu = borough_pu[(borough_pu[avg_fare_col] >= pu_25) & (borough_pu[avg_fare_col] <= pu_75)][pu_zone_col]
    avg_do = borough_do[(borough_do[avg_fare_col] >= do_25) & (borough_do[avg_fare_col] <= do_75)][do_zone_col]
    avg_zones = pd.concat([avg_pu, avg_do], axis=0).drop_duplicates().reset_index(drop=True).to_frame(name='average_zones')

    return pricey_zones, cheap_zones, avg_zones

