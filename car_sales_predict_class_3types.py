# python2.7
# load libraries
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import ttest_ind
from scipy.stats import f_oneway
import numpy as np, statsmodels.stats.api as sms
from scipy.stats import kstest
from scipy.stats import normaltest
from scipy.stats import mannwhitneyu
from numpy.random import randn
from scipy.stats import kurtosistest
# read csv
# data_org = pd.read_csv('Auto1-DA-TestData (2).csv')
# data_csv = 'Auto1-DA-TestData (2).csv'

class CarReorg:
	def __init__(self, data_org):
		self.data_org = pd.read_csv(data_org)

	# # all preprocessing
	# check basic & remove duplicates
	def basic_features_clean(self):#, data_org):
		# Check duplicate data
		data_org = self.data_org
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
	def calculate_sell_duration(self, data):
		sell_duration = pd.to_datetime(data['sold_date']) - pd.to_datetime(data['bought_date'])
		# sell_duration_dropna = sell_duration.dropna()
		data['sell_duration'] = sell_duration

		# ===== clean weird data (remove sell_days<0, NaT), But keep when it's unsold ('sold' == 0)
		data_soldPositive = data[(data['sell_duration'].dt.days > 0) | (data['sold'] == 0)]
		# data_soldPositive = data_onlypositive#.dropna() NaN
		data_soldPositive['sell_duration'].dt.days.astype('float') # NaT is float,so to convert into number
		data_soldPositive['sell_days'] = ((data_soldPositive['sell_duration'].dt.days)).astype('float') # change character --> float
		return data_soldPositive

class CarCluster:
	def __init__(self, data_org, ref_cluster, KPI_days):#ref_manufacturer, ref_country, ref_fuel):#, KPI_days):
		self.ref_manufacturer = ref_cluster[0]
		self.ref_country = ref_cluster[1]
		self.ref_fuel = ref_cluster[2]
		self.data_org = data_org
	# 1. Sales Speed
	# 1a. Fastest selling car !  Manufacturer| Sourcing_country | Fuel_Type)
	def print_fastest_sales(self):#, data):
		data = self.data_org
		sell_speed_summary = data.groupby(['manufacturer','sourcing_country', 'fuel_type'])['sell_days'].mean()
		print('Fastest selling car cluster ' + str(sell_speed_summary.idxmin()) + '\nCar Sold Days: ' + str(sell_speed_summary.min()))
		return sell_speed_summary

	# 1b. Is the fastest selling car, sold faster than [Masterati | USA | Diesel]?
	def print_compare_car(self, sell_speed_summary):#, ref_cluster):
		data = self.data_org
		# extract sell_days for reference car cluster [Masterati | USA | Diesel]
		data_ref = data[(data['manufacturer'] == self.ref_manufacturer) & (data['sourcing_country'] == self.ref_country) & (data['fuel_type'] == self.ref_fuel)]['sell_days']
		# data_ref = data[(data['manufacturer'] == ref_cluster[0]) & (data['sourcing_country'] == ref_cluster[1]) & (data['fuel_type'] == ref_cluster[2])]['sell_days']
		data_ref = data_ref.dropna()

		# extract sell_days for fastest car cluster [Skoda | USA | Diesel]
		fastest_manufacturer, fastest_country, fastest_fuel = sell_speed_summary.idxmin()
		data_fastest = data[(data['manufacturer'] == fastest_manufacturer) & (data['sourcing_country'] == fastest_country) & (data['fuel_type'] == fastest_fuel)]['sell_days']
		data_fastest = data_fastest.dropna()

		# check normality
		plt.hist(data_fastest, bins=100)
		# conduct F-test (data_fastest > data_ref? )
		F, p_value = f_oneway(data_fastest, data_ref)
		data_diff = data_ref.mean()-data_fastest.mean()

		# print the F-test result
		print('Car cluster ' + str(sell_speed_summary.idxmin()))
		if p_value < 0.05:			print(' is sold faster than ')
		else: print(' is not significantly different from ')
		print(str(self.ref_manufacturer) + '|' + str(self.ref_country) + '|' + str(self.ref_fuel)+
		' \ndays: '+ str(data_diff) + '  p= ' + str(p_value) )
		return p_value, data_ref, data_fastest

	# 1c. Calculate KPI (whether it's sold within 100 days)
	def print_worst_KPI(self):#, data):#, data, KPI_days):
		data = self.data_org
		# sold car (within 100 days)
		data['KPI'] = data['sell_days']<KPI_days
		KPI_summary = data.groupby(['manufacturer', 'sourcing_country', 'fuel_type'])['KPI'].mean()
		print('Worst KPI, lowest sales speed ' + str(KPI_summary.idxmin()) + '\nKPI: ' + str(KPI_summary.min()))

		return KPI_summary

class CarChannel:
	def __init__(self, data_org):#ref_manufacturer, ref_country, ref_fuel):#, KPI_days):
		self.data_org = data_org
	# 2. Sales Channel
	# 2a. Sell by channel
	def sell_by_channel(self):#, data):
		data = self.data_org
		data.keys()
		print(data.groupby(['sales_channel'])['sell_days'].mean())
		# type1 is faster to sell than type2

	# 2b. Type1 better than Type2 ?
	def channel_compare(self):#, data):
		data = self.data_org
		data_type1 = data[data['sales_channel'] == 'auction_type1']['sell_days']
		data_type1 = data_type1.dropna()
		data_type2 = data[data['sales_channel'] == 'auction_type2']['sell_days']
		data_type2 = data_type2.dropna()
		t, p_value = ttest_ind(data_type1, data_type2)

		cm = sms.CompareMeans(sms.DescrStatsW(data_type2), sms.DescrStatsW(data_type1))
		print cm.tconfint_diff(usevar='unequal')
		if p_value < 0.05:
			print('type1 is sold faster than from type2: ' + str(p_value))
		else:
			print('type1 is not significantly different from type2: ' + str(p_value))
		return p_value, data_type1, data_type2

if __name__ == "__main__":
    # Which File to analyze? What is the reference cluster? What is the reference KPI days #
	data_org = 'Auto1-DA-TestData (2).csv'
	ref_cluster = ['Ssangyong', 'USA', 'Diesel']#['Maserati', 'USA', 'Diesel']
	KPI_days = 100

	# create car_example instance
	car_ex = CarReorg(data_org)
	# data_clean = car_ex.basic_features_clean

	# 0. Basic Clean + add features
	data_orig = car_ex.basic_features_clean()#data_org))
	data_clean = car_ex.calculate_sell_duration(data_orig)
	data_clean.keys()
	# 1. Sales Speed
	cluster_ex = CarCluster(data_clean, ref_cluster, KPI_days)
	sell_speed_summary = cluster_ex.print_fastest_sales()#data_clean)
	p_value, data_ref, data_fastest = cluster_ex.print_compare_car(sell_speed_summary)

	normaltest(data_ref)#, 'norm')#dist='norm', pvalmethod='approx')
	mannwhitneyu(data_fastest, data_ref)
	plt.hist(data_ref, bins=30)
	data_ref.median() - data_fastest.median()
	a=np.random.normal(0, 1)
	cluster_ex.print_worst_KPI()#data_clean)

	# 2. Sales Channel
	channel_ex = CarChannel(data_clean)
	channel_ex.sell_by_channel()
	p, type1, type2 = channel_ex.channel_compare()
	(type1).shape
	mannwhitneyu(type1, type2)
	plt.hist([type1, type2], bins=40)

		stat, p = normaltest(type1)
		p < 0.001
