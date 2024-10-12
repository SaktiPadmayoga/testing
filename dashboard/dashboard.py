import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
sns.set(style='dark')

# Define function
def create_sum_order_products_df(all_df):
    sum_order_products_df = all_df.groupby("product_category_name").price.sum().sort_values(ascending=False).reset_index()
    return sum_order_products_df

def create_bystate_df(all_df):
    bystate_df = all_df.groupby(by="customer_state").order_id.nunique().sort_values(ascending=False).reset_index()
    bystate_df.rename(columns={
        "order_id" : "amount_orders"
    }, inplace=True)
    return bystate_df

def create_range_revscor_df(all_df):
    range_revscor_df = all_df.groupby("review_score").agg({
    "delivery_time": ["mean"]
    })
    return range_revscor_df

def create_rfm_df(all_df):
    rfm_df = all_df.groupby(by="customer_id", as_index=False).agg({
    "order_purchase_timestamp": "max", # mengambil tanggal order terakhir
    "order_id": "nunique", # menghitung jumlah order
    "price": "sum" # menghitung jumlah revenue yang dihasilkan
    })

    # menamai ulang kolum
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date #dari datetime to date(just tanggal)
    recent_date = all_df["order_purchase_timestamp"].dt.date.max() # mengambil tanggal maksimum dari all_df
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days) # max order timestamp tu terakhir masing" pelanggan melakukan transaksi, seangkan recent_date itu terakhir transaksi

    # rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df

def create_rfm_segment_df(all_df):
    rfm_segment_df = all_df.groupby(by="customer_id", as_index=False).agg({
    "order_purchase_timestamp": "max", # mengambil tanggal order terakhir
    "order_id": "nunique", # menghitung jumlah order
    "price": "sum" # menghitung jumlah revenue yang dihasilkan
    })

    # menamai ulang kolum
    rfm_segment_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    # menghitung kapan terakhir pelanggan melakukan transaksi (hari)
    rfm_segment_df["max_order_timestamp"] = rfm_segment_df["max_order_timestamp"].dt.date #dari datetime to date(just tanggal)
    recent_date = all_df["order_purchase_timestamp"].dt.date.max() # mengambil tanggal maksimum dari all_df
    rfm_segment_df["recency"] = rfm_segment_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days) # max order timestamp tu terakhir masing" pelanggan melakukan transaksi, seangkan recent_date itu terakhir transaksi

    rfm_segment_df["recency_score"] = pd.qcut(
    rfm_segment_df['recency'], 
    q=5,  # This is the number of quantiles (bins)
    labels=[5, 4, 3, 2, 1],  # These are your bin labels, must match the number of bins
    duplicates='drop'  # Handle duplicate edges if necessary
    )
    # Calculate frequency score based on rank quantiles, assigning labels from 1 to 5 (1 being lowest frequency)
    rfm_segment_df["frequency_score"] = pd.qcut(rfm_segment_df["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5])

    rfm_segment_df['segment'] = rfm_segment_df['recency_score'].astype(str) + rfm_segment_df['frequency_score'].astype(str)
    rfm_segment_df.drop("max_order_timestamp", axis=1, inplace=True)

    # create segment
    # Mapping of segments to their corresponding customer segments
    seg_map = {
    r'[1-2][1-2]': 'hibernating',
    r'[1-2][3-4]': 'at_risk',
    r'[1-2]5': 'cant_loose',
    r'3[1-2]': 'about_to_sleep',
    r'33': 'need_attention',
    r'[3-4][4-5]': 'loyal_customers',
    r'41': 'promising',
    r'51': 'new_customers',
    r'[4-5][2-3]': 'potential_loyalists',
    r'5[4-5]': 'champions'
    }

    # Map RFM segments to corresponding customer segments using predefined seg_map
    rfm_segment_df['segment'] = rfm_segment_df['segment'].replace(seg_map, regex=True)

    # Keep only relevant columns and return the resulting dataframe
    rfm_segment_df = rfm_segment_df[["recency", "frequency", "monetary", "segment"]]

    rfm_segment_df.index = rfm_segment_df.index.astype(int)  # Convert index to integer
    rfm_segment_df.head()

    rfm_segment_df = rfm_segment_df[["segment", "recency", "frequency", "monetary"]]



    return rfm_segment_df

# import csv
all_df = pd.read_csv("Dashboard/all_data.csv")

# Create sidebar and filtering
datetime_columns = ["order_purchase_timestamp", "order_delivered_carrier_date"]
all_df.sort_values(by="order_purchase_timestamp", inplace=True)
all_df.reset_index(inplace=True)
 
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])


min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()
 
with st.sidebar:
    # Menambahkan logo perusahaan
    st.image("https://github.com/dicodingacademy/assets/raw/main/logo.png")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )


main_df = all_df[(all_df["order_purchase_timestamp"] >= str(start_date)) & (all_df["order_purchase_timestamp"] <= str(end_date))]



# Call function
sum_order_products_df = create_sum_order_products_df(main_df)
bystate_df = create_bystate_df(main_df)
range_revscor_df = create_range_revscor_df(main_df)
rfm_df = create_rfm_df(main_df)
rfm_segment_df = create_rfm_segment_df(main_df)

# Create main content
st.header('E-Commerce Dashboard📝')


st.subheader('Best & Worst Performing Product Categories')

fig, ax = plt.subplots(figsize=(12, 5))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="price", y="product_category_name", data=sum_order_products_df.head(5), palette=colors)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.set_title("Best Performing Product Category", loc="center", fontsize=15)
ax.tick_params(axis ='y', labelsize=12)
st.pyplot(fig)


fig, ax = plt.subplots(figsize=(12, 5))
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x="price", y="product_category_name", data=sum_order_products_df.sort_values(by="price", ascending=True).head(5), palette=colors)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.invert_xaxis()
ax.yaxis.set_label_position("right")
ax.yaxis.tick_right()
ax.set_title("Worst Performing Product Category", loc="center", fontsize=15)
ax.tick_params(axis='y', labelsize=12)

st.pyplot(fig)



st.subheader('Customers distribution accross different states')

fig, ax = plt.subplots(nrows=1, figsize=(12, 6))
sns.barplot(
    y="amount_orders", 
    x="customer_state",
    data=bystate_df.sort_values(by="amount_orders", ascending=False)
)
plt.title("Number of Order by State", loc="center", fontsize=15)
plt.ylabel(None)
st.pyplot(fig)



st.subheader('The effect of delivery duration on review scores')

fig, ax = plt.subplots(nrows=1, figsize=(12, 6))
plt.plot(range_revscor_df.index, range_revscor_df.values)
plt.gca().invert_xaxis()
plt.title("Average Delivery Time by Review Score")
plt.xlabel("Review Score (Reverse)")
plt.ylabel("Average Delivery Time (days)")
st.pyplot(fig)




#################################
st.subheader('Best Customer Based on RFM Parameters (customer_id)')
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))
 
colors = ["#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4", "#72BCD4"]
 
sns.barplot(y="recency", x="customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis ='x', labelsize=12, rotation=45)
 
sns.barplot(y="frequency", x="customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis ='x', labelsize=12, rotation=45)
 
sns.barplot(y="monetary", x="customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis ='x', labelsize=12, rotation=45)
 
plt.suptitle("Best Customer Based on RFM Parameters (customer_id)", fontsize=20)
st.pyplot(fig)



st.subheader('How can customers be segmented based on their purchase habit?')
# mean of each rfm
mean_recency = rfm_segment_df.groupby("segment")["recency"].mean().reset_index()
mean_frequency = rfm_segment_df.groupby("segment")["frequency"].mean().reset_index()
mean_monetary = rfm_segment_df.groupby("segment")["monetary"].mean().reset_index()

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))
 
colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
 
sns.barplot(y="recency", x="segment", data=mean_recency.sort_values(by="recency", ascending=False), ax=ax[0])
ax[0].set_ylabel("average of not shopping (days)")
ax[0].set_xlabel("segments")
ax[0].set_title("Recency", loc="center", fontsize=15)
ax[0].tick_params(axis ='x', labelsize=12, rotation=45)
 
sns.barplot(y="frequency", x="segment", data=mean_frequency.sort_values(by="frequency", ascending=False), ax=ax[1])
ax[1].set_ylabel("times of shopped")
ax[1].set_xlabel("segments")
ax[1].set_title("Frequency", loc="center", fontsize=15)
ax[1].tick_params(axis ='x', labelsize=12, rotation=45)

sns.barplot(y="monetary", x="segment", data=mean_monetary.sort_values(by="monetary", ascending=False), ax=ax[2])
ax[2].set_ylabel("average of revenue")
ax[2].set_xlabel("segments")
ax[2].set_title("Monetary", loc="center", fontsize=15)
ax[2].tick_params(axis ='x', labelsize=12, rotation=45)
 
st.pyplot(fig)


# Final Result of RFM Analysis
rfm_detail_df = rfm_segment_df.groupby("segment").count().reset_index()
fig, ax = plt.subplots(nrows=1, figsize=(12, 6))
sns.barplot(
    y="recency", 
    x="segment",
    data=rfm_detail_df.sort_values(by="recency", ascending=False)
)
plt.ylabel("amount of customers")
plt.xlabel("Segments")
plt.xticks(rotation=45)
plt.suptitle("Final Result of RFM Analysis", fontsize=20)
st.pyplot(fig)



