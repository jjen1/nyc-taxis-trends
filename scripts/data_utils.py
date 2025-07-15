import pandas as pd

def remove_outliers(df, duration_col='duration_mins', distance_col='trip_distance', lower=0.01, upper=0.99):
    """
    Remove rows with non-positive duration or distance, then filter out extreme outliers
    based on quantiles for both duration and distance columns.
    Returns a cleaned DataFrame with index reset.
    """
    # Remove negative values
    df_clean = df[(df[duration_col] > 0) & (df[distance_col] > 0)].copy()
    # Calculate quantile thresholds
    duration_min = df_clean[duration_col].quantile(lower)
    duration_max = df_clean[duration_col].quantile(upper)
    distance_min = df_clean[distance_col].quantile(lower)
    distance_max = df_clean[distance_col].quantile(upper)
    # Filter out outliers
    mask = (
        df_clean[duration_col].between(duration_min, duration_max) &
        df_clean[distance_col].between(distance_min, distance_max)
    )
    return df_clean[mask].reset_index(drop=True)

def identify_cancelled_rides(df, ride_id_cols = ['VendorID','PU_datetime', 'DO_datetime', 'PULocationID', 'DOLocationID', 'duration_mins', 'trip_distance', 'passenger_count', 'payment_type', 'RatecodeID']):
    """
    'ride_id_cols' serve as a unique ride identification, EXCEPT fare_amount since we want to match pairs of rides with opposite fare amounts
    Remove rides with negative fare amounts, which are likely cancelled or refunded.
    Returns a cleaned DataFrame with index reset.
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
