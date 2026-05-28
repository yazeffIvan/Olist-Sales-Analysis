import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine


server = '*'
database = 'Olist'
username = 'sa'
password = 'pass'

engine = create_engine(
    f"mssql+pyodbc://{username}:{password}@{server}/{database}"
    "?driver=ODBC+Driver+17+for+SQL+Server"
)


orders = pd.read_sql("SELECT * FROM olist_orders_dataset", engine)
customers = pd.read_sql("SELECT * FROM olist_customers_dataset", engine)
payments = pd.read_sql("SELECT * FROM olist_order_payments_dataset", engine)
items = pd.read_sql("SELECT * FROM olist_order_items_dataset", engine)
products = pd.read_sql("SELECT * FROM olist_products_dataset", engine)
reviews = pd.read_sql("SELECT * FROM olist_order_reviews_dataset", engine)
category_trans = pd.read_sql("SELECT * FROM product_category_name_translation", engine)


orders['order_purchase_timestamp'] = pd.to_datetime(orders['order_purchase_timestamp'])
orders['order_delivered_customer_date'] = pd.to_datetime(orders['order_delivered_customer_date'])
orders['order_estimated_delivery_date'] = pd.to_datetime(orders['order_estimated_delivery_date'])

orders['delivery_delay_days'] = (orders['order_delivered_customer_date'] - orders['order_estimated_delivery_date']).dt.days

delivered_orders = orders[orders['order_status'] == 'delivered'].copy()


total_revenue = payments['payment_value'].sum()
total_orders = orders['order_id'].nunique()
aov = payments.groupby('order_id')['payment_value'].sum().mean()

# Задержки доставки
delayed_orders = delivered_orders[delivered_orders['delivery_delay_days'] > 0]
avg_delay = delayed_orders['delivery_delay_days'].mean() if len(delayed_orders) > 0 else 0

# Repeat Rate
customer_orders = orders.groupby('customer_id')['order_id'].nunique()
repeat_rate = (customer_orders > 1).mean() * 100



sns.set_style('whitegrid')

# 1. Динамика выручки по месяцам
monthly_rev = payments.merge(orders[['order_id', 'order_purchase_timestamp']], on='order_id')
monthly_rev['month'] = monthly_rev['order_purchase_timestamp'].dt.to_period('M')
monthly_rev = monthly_rev.groupby('month')['payment_value'].sum()

plt.figure(figsize=(12, 6))
monthly_rev.plot(kind='line', marker='o', linewidth=2.5, color='darkblue')
plt.title('Динамика выручки по месяцам', fontsize=14, fontweight='bold')
plt.xlabel('Месяц')
plt.ylabel('Выручка (BRL)')
plt.xticks(rotation=45)
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# 2. Топ-10 категорий
items_products = items.merge(products, on='product_id')
items_products = items_products.merge(category_trans, on='product_category_name', how='left')
category_revenue = items_products.groupby('product_category_name_english')['price'].sum()\
                    .sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 6))
plt.barh(category_revenue.index, category_revenue.values, color='teal')
plt.title('Топ-10 категорий по выручке', fontsize=14, fontweight='bold')
plt.xlabel('Выручка (BRL)')
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()

# 3. Распределение оценок отзывов
if not reviews.empty:
    plt.figure(figsize=(10, 5))
    score_counts = reviews['review_score'].value_counts().sort_index()
    colors = ['#d73027' if x <= 2 else '#fdae61' if x == 3 else '#1a9850' for x in score_counts.index]
    sns.barplot(x=score_counts.index, y=score_counts.values, palette=colors)
    plt.title('Распределение оценок отзывов')
    plt.xlabel('Оценка')
    plt.ylabel('Количество')
    plt.tight_layout()
    plt.show()


print(f"Общая выручка:          {total_revenue:,.2f} BRL")
print(f"Средний чек (AOV):      {aov:,.2f} BRL")
print(f"Повторные покупки:      {repeat_rate:.2f}%")
print(f"Средняя задержка:       {avg_delay:.1f} дней")
