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

