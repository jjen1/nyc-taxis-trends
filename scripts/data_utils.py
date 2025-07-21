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

def identify_cancelled_rides(df, ride_id_cols, fee_cols):
    """
    - 'ride_id_cols' serve as a unique ride identification
    - fare_amount and other monetary columns will be stored in 'fee_cols' since we want to match pairs of rides with opposite fare amounts
    - remove rides with negative fare amounts, which are likely cancelled or refunded.
    - returns a cleaned DataFrame with index reset.
    """
    
    # fill nulls in ride_id_cols with a placeholder
    for col in ride_id_cols:
        df[col] = df[col].fillna('N/A') # will need to replace passenger_count later on with 0s

    # fill nulls in fee_cols with 0
    df[fee_cols] = df[fee_cols].fillna(0)

    # filters for negative and positive fee columns
    neg_fare = df[(df[fee_cols] < 0).any(axis=1)].copy()
    pos_fare = df[(df[fee_cols] > 0).any(axis=1)].copy()

    # merge the dfs
    merged_fares = neg_fare.merge(pos_fare, on=ride_id_cols, suffixes=('_neg', '_pos'))

    # find pairs where all fee columns are exact opposites
    fee_opposite_mask = (
        merged_fares[[f + '_neg' for f in fee_cols]].values == -merged_fares[[f + '_pos' for f in fee_cols]].values
    ).all(axis=1)
    matched_pairs = merged_fares[fee_opposite_mask]

    return matched_pairs

def remove_cancelled_fare_pairs(df, matched_pairs):
    """
    remove cancelled fare pairs from the original DataFrame using index-based removal
    removes both sides of the matched pairs (negative and positive fares)
    """
    # gets the index of the matched pairs (from the merged dataframe)
    matched_idx = matched_pairs.index

    # remove rows from df whose index is in matched_idx
    df_cleaned = df[~df.index.isin(matched_idx)]

    # remove any remaining negative fares not affiliated with a matching pair
    df_cleaned = df_cleaned[df_cleaned['fare_amount'] >= 0]

    return df_cleaned.reset_index(drop=True)

def categorize_zones(borough_pu_avg, borough_do_avg, borough_avg_fare, avg_fare_col='avg_fare', pu_zone_col='PU_Zone', do_zone_col='DO_Zone'):
    """
    categorizing zones based on average fare amounts and their quartiles
    returns 3 dataframes: pricey_zones, cheap_zones, avg_zones
    - pricey_zones: zones with fares above the 75th percentile of borough average fare
    - cheap_zones: zones with fares below the 25th percentile of borough average fare
    - avg_zones: zones with fares between the 25th and 75th percentiles of borough average fare 
    """
    # finding the 75th percentile of fares that are above the borough average fare 
    pu_75 = borough_pu_avg[borough_pu_avg[avg_fare_col] > borough_avg_fare][avg_fare_col].quantile(0.75)
    do_75 = borough_do_avg[borough_do_avg[avg_fare_col] > borough_avg_fare][avg_fare_col].quantile(0.75)

    # finding the 25th percentile of fares that are lower than the borough average fare 
    pu_25 = borough_pu_avg[borough_pu_avg[avg_fare_col] < borough_avg_fare][avg_fare_col].quantile(0.25)
    do_25 = borough_do_avg[borough_do_avg[avg_fare_col] < borough_avg_fare][avg_fare_col].quantile(0.25)

    # pricier zones: based on the 75th percentile of fares
    pricey_pu_zones = borough_pu_avg[(borough_pu_avg[avg_fare_col] > borough_avg_fare) & (borough_pu_avg[avg_fare_col] > pu_75)][pu_zone_col]
    pricey_do_zones = borough_do_avg[(borough_do_avg[avg_fare_col] > borough_avg_fare) & (borough_do_avg[avg_fare_col] > do_75)][do_zone_col]
    pricey_zones = pd.concat([pricey_pu_zones, pricey_do_zones], axis=0).drop_duplicates().reset_index(drop=True).to_frame(name='pricier_zones')

    # cheap zones: based on the 25th percentile of fares
    cheap_pu_zones = borough_pu_avg[(borough_pu_avg[avg_fare_col] < borough_avg_fare) & (borough_pu_avg[avg_fare_col] < pu_25)][pu_zone_col]
    cheap_do_zones = borough_do_avg[(borough_do_avg[avg_fare_col] < borough_avg_fare) & (borough_do_avg[avg_fare_col] < do_25)][do_zone_col]
    cheap_zones = pd.concat([cheap_pu_zones, cheap_do_zones], axis=0).drop_duplicates().reset_index(drop=True).to_frame(name='cheaper_zones')

    # average zones: based on the 25th and 75th percentiles of fares
    avg_pu = borough_pu_avg[(borough_pu_avg[avg_fare_col] >= pu_25) & (borough_pu_avg[avg_fare_col] <= pu_75)][pu_zone_col]
    avg_do = borough_do_avg[(borough_do_avg[avg_fare_col] >= do_25) & (borough_do_avg[avg_fare_col] <= do_75)][do_zone_col]
    avg_zones = pd.concat([avg_pu, avg_do], axis=0).drop_duplicates().reset_index(drop=True).to_frame(name='average_zones')

    return pricey_zones, cheap_zones, avg_zones

def neighborhood_fare_quantiles(exp, avg, cheap, fare_col='fare_amount', quantiles=[0.25, 0.5, 0.75]):
    return pd.DataFrame({
        'expensive_neighborhoods': exp[fare_col].quantile(quantiles),
        'average_neighborhoods': avg[fare_col].quantile(quantiles),
        'cheap_neighborhoods': cheap[fare_col].quantile(quantiles)
    }, index=pd.Index(quantiles, name='Quantile'))

def borough_tip_cleaned(borough_cleaned, tip='tip_amount', fare='fare_amount'):
    """ clean the borough dataframe for tip analysis
    - filters out rides with fare_amount < 1
    - calculates tip to fare and tip to total ratios
    - removes outliers based on tip amounts
    - filters out extreme outliers based on tip to fare and tip to total ratios
    - returns a cleaned DataFrame with monetary columns at the end for better readability"""
    # picking a percentile
    tip_quant = borough_cleaned[tip].quantile(0.99999)

    # removing rides with fare_amount < 1, since they can skew the data due to atypical fare amounts
    borough_cleaned = borough_cleaned[borough_cleaned[fare] >= 1].copy()

    # find the tip to fare and tip to total ratios for the rest of the columns
    borough_cleaned['tip_fare_ratio'] = (borough_cleaned[tip] / borough_cleaned[fare]) * 100
    borough_cleaned['tip_fare_ratio'] = borough_cleaned['tip_fare_ratio'].round(2)
    borough_cleaned['tip_total_ratio'] = (borough_cleaned[tip] / (borough_cleaned[tip] + borough_cleaned[fare])) * 100
    borough_cleaned['tip_total_ratio'] = borough_cleaned['tip_total_ratio'].round(2)

    # rearranging the columns to have the monetary columns at the end for better readability
    monetary_cols = [fare, tip, 'tip_fare_ratio', 'tip_total_ratio','total_amount', 'extra', 'mta_tax', 'improvement_surcharge', 'tolls_amount', 'congestion_surcharge', 'cbd_congestion_fee', 'Airport_fee']
    borough_tips = borough_cleaned[monetary_cols + [c for c in borough_cleaned.columns if c not in monetary_cols]].sort_values(by=[tip, fare], ascending=False).copy()

    # creating a mask to filter out the outliers in tip amounts
    outlier_mask = ((borough_tips[tip] > borough_tips[fare]) & (borough_tips[tip] > tip_quant))
    borough_tips = borough_tips[~outlier_mask]  # checking the statistics of the non-outlier tips

    # set a threshold for each ratio: extremely generous thresholds to filter out the extreme outliers
    tip_total_ratio_threshold = borough_tips['tip_total_ratio'].quantile(0.999) 
    tip_fare_ratio_threshold = borough_tips['tip_fare_ratio'].quantile(0.999)

    # further filtering with ratios
    borough_tips = borough_tips[(borough_tips['tip_fare_ratio'] < tip_fare_ratio_threshold) & (borough_tips['tip_total_ratio'] < tip_total_ratio_threshold)]
    return borough_tips

def match_tip_neighborhoods (borough_tips, borough_neighborhoods, ride_id_cols):
    """ match tips with neighborhoods based on ride_id_cols
    - ride_id_cols serve as a unique ride identification
    - filters borough_tips for records in borough_neighborhoods
    - returns a DataFrame with matched tips and neighborhoods
    """
    # copy the dfs
    borough_tips = borough_tips.copy()
    borough_neighborhoods = borough_neighborhoods.copy()

    # saving the keys to a new column for easier filtering later
    borough_tips['ride_key'] = borough_tips[ride_id_cols].astype(str).agg('_'.join, axis=1) 
    borough_neighborhoods['ride_key'] = borough_neighborhoods[ride_id_cols].astype(str).agg('_'.join, axis=1)

    # filter borough_tips for records in borough_neighborhoods
    b_zone_tips = borough_tips[borough_tips['ride_key'].isin(borough_neighborhoods['ride_key'])]

    return b_zone_tips

def constant_tips(borough_tips, borough_exp_tips, borough_avg_tips, borough_cheap_tips, tip_col='tip_amount'):
    """ finding what percentage of rides in their respective categories are above the general average tip amount """

    # finding what percentage of rides in their respective categories are above the general average tip amount in Manhattan
    borough_avg = borough_tips[tip_col].mean()

    # percentage of rides with tips above the average tip amount in expensive zones
    exp = (borough_exp_tips[tip_col] >= borough_avg).sum() / borough_exp_tips.shape[0] * 100  

    # percentage of rides with tips above the average tip amount in cheap zones
    cheap = (borough_cheap_tips[tip_col] <= borough_avg).sum() / borough_cheap_tips.shape[0] * 100  

    # calculate mean tip values for expensive and cheap zones
    exp_avg = borough_exp_tips[tip_col].mean()
    cheap_avg = borough_cheap_tips[tip_col].mean()
    # percentage of rides with tips between the average tip in expensive and cheap zones in average zones

    avg = borough_avg_tips[tip_col].between(min(exp_avg, cheap_avg), max(exp_avg, cheap_avg)).sum() / borough_avg_tips.shape[0] * 100
    return f'Expensive Neighborhoods: {round(exp, 2)} %\nAverage Neighborhoods: {round(avg, 2)} %\nCheap Neighborhoods: {round(cheap, 2)} %'

