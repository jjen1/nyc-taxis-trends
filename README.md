# NYC Taxi Tips & Borough Trends
**Understanding Tipping Behavior Across Boroughs and Segments**

## Project Overview

This project explores tipping behavior in New York City ride-hailing and taxi services. Using [NYC TLC Trip Record Data 2025](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page), the goal is to uncover insights on trends across boroughs, segmenting rides by different characteristics and how they influence taxi fares and tipping behavior.

The analysis is performed using Python libraries like `pandas`, `matplotlib`, and `seaborn`. All development is done in VSCode, with version control handled through Git.

## Objectives

### 1. Understanding the Data
- Explore ride characteristics: pickup/dropoff locations, time of day, duration, and distance.
- Segment and clean data across different services (Uber, Lyft, yellow taxis).
- Compare rides across boroughs: Manhattan, Brooklyn, Queens, The Bronx, Staten Island.

### 2. Location-Based Tipping Behavior
- Identify pricier neighborhoods and their tipping tendencies.
- Compare average tip amounts across pickup/dropoff zones.
- Analyze consistency of tipping (e.g., by calculating interquartile range or using mode).
- Include analysis of major transit points like **airports** (JFK, LGA, EWR).

### 3. Time-Based Tipping Behavior
- Segment by time of day (Morning, Afternoon, Night).
- Compare tipping on **weekends vs. weekdays**.
- Evaluate tipping after working hours and during nightlife periods.

### 4. Customer & Payment Segmentation
- Analyze by:
  - **Passenger count** (e.g., group rides might influence tipping).
  - **Payment types** (credit card vs. cash).
  - **Additional fees** and their impact on tipping.

### 5. Driver/Vendor Impact
- Compare tipping across different vendor types.

## Tech Stack
- **Languages & Libraries**: Python, pandas, matplotlib, seaborn
- **Environment**: VSCode
- **Version Control**: Git
