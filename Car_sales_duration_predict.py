# import libraries

import pandas as pd
import category_encoders as ce
import matplotlib.pyplot as plt
%matplotlib inline
import seaborn as sns
from scipy.stats import ttest_ind
from scipy.stats import f_oneway

#set font size of labels on matplotlib plots
plt.rc('font', size=16)
#set style of plots
sns.set_style('white')

# read csv
data_org = pd.read_csv('Auto1-DA-TestData (2).csv')
# parameters
KPI_days = 100
ref_manufacturer = 'Maserati'; ref_country = 'USA'; ref_fuel = 'Diesel'
ref_cluster = [ref_manufacturer, ref_country, ref_fuel]

# check basic & remove duplicates
def basic_features_clean(data_org):
    # Check duplicate data
    data = data_org.drop_duplicates()
    print('There is ' + str(data_org.shape[0] - data.shape[0]) + ' duplicate raws')
    # check fuel type
    print(data['fuel_type'].value_counts())
    # check country
    print(data['sourcing_country'].value_counts()) # => USA, China
    # check sold rate
    print('mean sold rate : '+ str(data['sold'].mean()))

    # check manufacturer
    manufacturer_counts = data['manufacturer'].value_counts()
    manufacturer_counts.plot(kind='bar')
    plt.show()
    return data

# Calculate sell duration  ('sell_duration' in days)
# when sell_days is negative (-), it's strange, so the raw is removed.
def calculate_sell_duration(data):
    sell_duration = pd.to_datetime(data['sold_date']) - pd.to_datetime(data['bought_date'])
    # sell_duration_dropna = sell_duration.dropna()
    data['sell_duration'] = sell_duration

    # ===== clean weird data (remove sell_days<0, NaT), But keep when it's unsold ('sold' == 0)
    data_soldPositive = data[(data['sell_duration'].dt.days > 0) | (data['sold'] == 0)]
    # data_soldPositive = data_onlypositive#.dropna() NaN
    data_soldPositive['sell_duration'].dt.days.astype('float') # NaT is float,so to convert into number
    data_soldPositive['sell_days'] = ((data_soldPositive['sell_duration'].dt.days)).astype('float') # change character --> float

    return data_soldPositive

# 1a. Fastest selling car !  Manufacturer| Sourcing_country | Fuel_Type)
def print_fastest_sales(data):

    sell_speed_summary = data.groupby(['manufacturer','sourcing_country', 'fuel_type'])['sell_days'].mean()
    print('Fastest selling car cluster ' + str(sell_speed_summary.idxmin()) + '\nCar Sold Days: ' + str(sell_speed_summary.min()))
    return sell_speed_summary

# 1b. Is the fastest selling car, sold faster than [Masterati | USA | Diesel]?
def print_compare_car(data, sell_speed_summary, ref_cluster):
    # extract sell_days for reference car cluster [Masterati | USA | Diesel]
    data_ref = data[(data['manufacturer'] == ref_cluster[0]) & (data['sourcing_country'] == ref_cluster[1]) & (data['fuel_type'] == ref_cluster[2])]['sell_days']
    data_ref = data_ref.dropna()

    # extract sell_days for fastest car cluster [Skoda | USA | Diesel]
    fastest_manufacturer, fastest_country, fastest_fuel = sell_speed_summary.idxmin()
    data_fastest = data[(data['manufacturer'] == fastest_manufacturer) & (data['sourcing_country'] == fastest_country) & (data['fuel_type'] == fastest_fuel)]['sell_days']
    data_fastest = data_fastest.dropna()

    # conduct F-test (data_fastest > data_ref? )
    # t, p = ttest_ind(data_fastest, data_ref)
    F, p = f_oneway(data_fastest, data_ref)
    data_diff = data_ref.mean()-data_fastest.mean()

    # print the t-test result
    print('Car cluster ' + str(sell_speed_summary.idxmin())
    + ' is sold faster than ' + str(ref_cluster[0]) + '|' + str(ref_cluster[1]) + '|' + str(ref_cluster[2])+
    ' \ndays: '+ str(data_diff) + '  p= ' + str(p) )
    return p

# 1c. Calculate KPI (whether it's sold within 100 days)
def print_worst_KPI(data):
    # sold car (within 100 days)
    data['KPI'] = data['sell_days']<KPI_days
    KPI_summary = data.groupby(['manufacturer', 'sourcing_country', 'fuel_type'])['KPI'].mean()
    print('Worst KPI, lowest sales speed ' + str(KPI_summary.idxmin()) + '\nKPI: ' + str(KPI_summary.min()))

    return KPI_summary


# 2a. Sell by channel
def sell_by_channel(data):
    data.keys()
    data.groupby(['sales_channel'])['sell_days'].mean()
# type1 is faster to sell than type2


# 2b. Type1 better than Type2 ?
def channel_compare(data):
    data_type1 = data[data['sales_channel'] == 'auction_type1']['sell_days']
    data_type1 = data_type1.dropna()
    data_type2 = data[data['sales_channel'] == 'auction_type2']['sell_days']
    data_type2 = data_type2.dropna()
    t,p = ttest_ind(data_type1, data_type2)
    return p

def main():
    # all preprocessing
    # Basic steps: check how many features exist in each columns & drop duplicate
    data = basic_features_clean(data_org)
    # 1. Sales Speed
    data = calculate_sell_duration(data)
    sell_speed_summary = print_fastest_sales(data)
    p = print_compare_car(data, sell_speed_summary, ref_cluster)
    KPI_summary = print_worst_KPI(data)


    # 2. Sales Channel
    sell_by_channel(data)
    p = channel_compare(data)
    # sale speed increased by auction_type1. (sell_days decreased!)
