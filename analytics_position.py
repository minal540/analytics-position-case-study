import pandas as pd

# Load datasets
deposit_df = pd.read_excel('C:/Users/Dell/Documents/analytics position case study.xlsx', sheet_name='deposit data', skiprows=3)
withdrawal_df = pd.read_excel('C:/Users/Dell/Documents/analytics position case study.xlsx', sheet_name='withdrawl data', skiprows=3)
gameplay_df = pd.read_excel('C:/Users/Dell/Documents/analytics position case study.xlsx', sheet_name='user gameplay data', skiprows=3)
print(deposit_df)
print(withdrawal_df)
print(gameplay_df)
print(gameplay_df.head())
print(gameplay_df.dtypes)


# Clean column names
deposit_df.columns = ['User Id', 'Datetime', 'Amount']
withdrawal_df.columns = ['User Id', 'Datetime', 'Amount']
gameplay_df.columns = ['User Id', 'Datetime', 'Games Played']

# Convert to datetime
deposit_df['Datetime'] = pd.to_datetime(deposit_df['Datetime'])
withdrawal_df['Datetime'] = pd.to_datetime(withdrawal_df['Datetime'])
gameplay_df['Games Played'] = pd.to_numeric(gameplay_df['Games Played'], errors='coerce')

# Define slot function
def get_slot(x):
    if pd.isnull(x):
        return 'Unknown'
    if x.hour < 12:
        return 'S1'
    else:
        return 'S2'

# Only apply get_slot if the 'Datetime' is really a datetime object
if pd.api.types.is_datetime64_any_dtype(gameplay_df['Datetime']):
    gameplay_df['Slot'] = gameplay_df['Datetime'].apply(get_slot)
else:
    print('Gameplay datetime is not valid, skipping slot assignment for gameplay.')
    gameplay_df['Slot'] = 'Unknown'  # Or handle as per your case

# Apply slot and extract date
deposit_df['Slot'] = deposit_df['Datetime'].apply(get_slot)
withdrawal_df['Slot'] = withdrawal_df['Datetime'].apply(get_slot)
# gameplay_df['Slot'] = 'Unknown'

deposit_df['Datetime'] = deposit_df['Datetime'].dt.date
withdrawal_df['Datetime'] = withdrawal_df['Datetime'].dt.date
gameplay_df['Datetime'] = pd.to_datetime(gameplay_df['Datetime'], errors='coerce').dt.date


# Aggregate deposits
deposit_summary = deposit_df.groupby(['User Id', 'Datetime', 'Slot']).agg({'Amount': ['sum', 'count']}).reset_index()
deposit_summary.columns = ['User Id', 'Datetime', 'Slot', 'Total Deposit', 'Deposit Count']

# Aggregate withdrawals
withdrawal_summary = withdrawal_df.groupby(['User Id', 'Datetime', 'Slot']).agg({'Amount': ['sum', 'count']}).reset_index()
withdrawal_summary.columns = ['User Id', 'Datetime', 'Slot', 'Total Withdrawal', 'Withdrawal Count']

# Aggregate games
game_summary = gameplay_df.groupby(['User Id', 'Datetime', 'Slot']).agg({'Games Played': 'sum'}).reset_index()

# Merge all data
combined = pd.merge(deposit_summary, withdrawal_summary, on=['User Id', 'Datetime', 'Slot'], how='outer').fillna(0)
combined = pd.merge(combined, game_summary, on=['User Id', 'Datetime', 'Slot'], how='outer').fillna(0)

# Calculate loyalty points
combined['Extra Deposit Points'] = 0.001 * combined.apply(lambda x: max(x['Deposit Count'] - x['Withdrawal Count'], 0), axis=1)
combined['Loyalty Points'] = (0.01 * combined['Total Deposit']) + (0.005 * combined['Total Withdrawal']) + combined['Extra Deposit Points'] + (0.2 * combined['Games Played'])

# Calculate loyalty points for specific slots
dates_slots = [
    {'Datetime': '2022-10-02', 'Slot': 'S1'},
    {'Datetime': '2022-10-16', 'Slot': 'S2'},
    {'Datetime': '2022-10-18', 'Slot': 'S1'},
    {'Datetime': '2022-10-26', 'Slot': 'S2'}
]

for item in dates_slots:
    result = combined[(combined['Datetime'] == pd.to_datetime(item['Datetime']).date()) & (combined['Slot'] == item['Slot'])]
    print(f"\nLoyalty Points for {item['Datetime']} Slot {item['Slot']}")
    print(result[['User Id', 'Loyalty Points']])

# Monthly loyalty points and ranking
monthly_summary = combined.groupby('User Id').agg({'Loyalty Points': 'sum', 'Games Played': 'sum'}).reset_index()
monthly_summary['Rank'] = monthly_summary.sort_values(['Loyalty Points', 'Games Played'], ascending=[False, False]).reset_index().index + 1

print("\nMonthly Loyalty Points and Ranking:")
print(monthly_summary.sort_values('Rank'))

# Calculate averages
average_deposit = deposit_df['Amount'].mean()
average_deposit_per_user = deposit_df.groupby('User Id')['Amount'].sum().mean()
average_games_per_user = gameplay_df.groupby('User Id')['Games Played'].sum().mean()

print(f"\nAverage Deposit Amount: {average_deposit}")
print(f"Average Deposit Amount per User: {average_deposit_per_user}")
print(f"Average Number of Games per User: {average_games_per_user}")

# Bonus distribution
top_50 = monthly_summary[monthly_summary['Rank'] <= 50]
total_loyalty_points = top_50['Loyalty Points'].sum()
top_50['Bonus Allocation'] = top_50['Loyalty Points'].apply(lambda x: (x / total_loyalty_points) * 50000)

print("\nBonus Allocation for Top 50 Players:")
print(top_50[['User Id', 'Loyalty Points', 'Bonus Allocation']])
