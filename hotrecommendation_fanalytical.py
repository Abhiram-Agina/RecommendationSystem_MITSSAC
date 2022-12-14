# -*- coding: utf-8 -*-
"""HotRecommendation_FANALYTICAL.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1IlCdlQqe9yNSis5rLlGf6BQSHkIQyqMe

#### Objective:

Develop a Product Recommendation Engine tailored to the customer. This project aims to increase total revenue and improve fan experience and engagement.

This program covers:
- Data Cleaning
- Data Organization
- Model Building 
- Recommendation

@Author: Abhiram Agina

@Advisors: Sabina Skolnik (Solutions Engineer), Dr. Anthony Franklin (Data & Analytics Leader)

@Company: Fanalytical

Reference:

https://www.kaggle.com/code/rsadiq/recommender-system-for-implicit-feedback/notebook

Feedback:
- Understand '% Accuracy'. How can Fanalytical Interpret our results? What will the user see based on results.
- Develop 'Meal Plan'. User won't buy 10 Drinks. Understand patterns in user orders. (Key: Seperating Dataset through Food Groups/Types)
- Cold Order Feature
"""

#Downloading External Libraries
!pip install implicit

#Libraries
import sys
import pandas as pd
import numpy as np
import os

#Sparse Matrices are utilized because each user will interact with a small subset of items making the user-item interactions sparse.
import scipy.sparse as sparse

#Implcit Library includes several different popular recommendation algorithms for implicit feedback datasets
import implicit #Utilized to evaluate implicit feedback

lineItemsVN = pd.read_excel('/content/F&M Line Items.xlsx')
lineItemsVN.head(3)

"""##### Data Cleaning

###### Dropping Fields
"""

#Dropping Empty Features
lineItemsVN = lineItemsVN.drop(["inline_upsell_item_name", "inline_upsell_item_sku", "inline_upsell_menu_item_uuid", 
                                "promotion_uuid", "promotion_details", "tax_rules", 'settled_by', 'refunded_by',
                                'variant_name', 'variant_group'], axis = 1)

#Dropping Uniformly Populated Features
lineItemsVN = lineItemsVN.drop(["inline_upsell", "product_type", "web_order", "promotion_discount", "tax_inclusive", "split_item_quantity", "menu_subtype", "denominator", "numerator"], axis = 1)

#Dropping Redundant Features
lineItemsVN = lineItemsVN.drop(['Unnamed: 0', 'menu', 'internal_name', 'order_id', 'item_report_rollup'], axis = 1)

"""###### Data Polishing"""

#Filling Null Values
lineItemsVN['menu_categories'] = lineItemsVN['menu_categories'].fillna(lineItemsVN['item_categories'])
lineItemsVN = lineItemsVN.drop('item_categories', axis = 1)
lineItemsVN['menu_categories'].isnull().sum()

#Removing '- P' from Item Names, so Items with or without '- P' are considered the same
lineItemsVN['item_name'] = lineItemsVN['item_name'].str.replace("- P", "")
lineItemsVN['item_name'].value_counts()

#Clearing all Non-Orders (ex: No Salsa, Spicy, Regular, etc.)
lineItemsVN['menu_categories'].value_counts()
lineItemsVN['menu_categories'].isna().sum()
lineItemsVN = lineItemsVN[lineItemsVN['menu_categories'].isin(['Beer - Packaged', 'Subcontractor', 'N/A Beverage', 'Food', 'Beer - Draft', 'Liquor', 'Mixers,Soda Flavor', 'Mixers', 'Wine', 'Retail'])]

"""##### Data Organization"""

#Isolting the User, Item, # of Orders
#Grouping each customer and each item interactions
organizedLIData = lineItemsVN[['user_uuid', 'menu_categories', 'item_name', 'line_item_uuid']]
organizedLIData = organizedLIData.groupby(['user_uuid', 'menu_categories', 'item_name'])['line_item_uuid'].count().to_frame().reset_index()

#Creating item_ids and user_ids
organizedLIData['user_uuid'] = organizedLIData['user_uuid'].astype('category')
organizedLIData['user_id'] = organizedLIData['user_uuid'].cat.codes
organizedLIData['item_name'] = organizedLIData['item_name'].astype('category')
organizedLIData['item_id'] = organizedLIData['item_name'].cat.codes


organizedLIData = organizedLIData.reindex(columns=['user_id', 'user_uuid', 'menu_categories', 'item_id', 'item_name','line_item_uuid'])
organizedLIData.columns = ['user_id', 'user_name', 'item_type', 'item_id', 'item_name', 'orders']

organizedLIData

#Dividing by ITEM TYPE
foodData = organizedLIData[organizedLIData['item_type'].isin(['Subcontractor', 'Food', 'Retail'])].reset_index().drop('index', axis = 1)
drinkData = organizedLIData[organizedLIData['item_type'].isin(['Beer - Packaged', 'N/A Beverage', 'Beer - Draft', 'Liquor', 'Mixers,Soda Flavor', 'Mixers', 'Wine'])].reset_index().drop('index', axis = 1)

#Creating Model
# The implicit library expects data as a item-user matrix so we
# create two matricies, one for fitting the model (item-user) 
# and one for recommendations (user-item)
sparse_item_userF = sparse.csr_matrix((foodData['orders'].astype(float), (foodData['user_id'], foodData['item_id'])))
#sparse_user_itemF = sparse.csr_matrix((foodData['orders'].astype(float), (foodData['item_id'], foodData['user_id'])))

sparse_item_userD = sparse.csr_matrix((drinkData['orders'].astype(float), (drinkData['user_id'], drinkData['item_id'])))
#sparse_user_itemD = sparse.csr_matrix((drinkData['orders'].astype(float), (drinkData['item_id'], drinkData['user_id'])))

os.environ['MKL_NUM_THREADS'] = '1' #To avoid multithreading.
os.environ['OPENBLAS_NUM_THREADS'] = '1'

#Iterations = Combing through dataset to find connections
#Excessive iterations lead to overfitting and do not create a universally representative model
foodModel = implicit.als.AlternatingLeastSquares(factors = 50, iterations = 100)
''''Parameters: (factors=100, regularization=0.01, dtype=<type 'numpy.float32'>, use_native=True, use_cg=True, 
use_gpu=False, iterations=15, calculate_training_loss=False, num_threads=0)''';

drinkModel = implicit.als.AlternatingLeastSquares(factors = 50, iterations = 100)
''''Parameters: (factors=100, regularization=0.01, dtype=<type 'numpy.float32'>, use_native=True, use_cg=True, 
use_gpu=False, iterations=15, calculate_training_loss=False, num_threads=0)''';

alpha = 40 #Matrix Multiplier
train_food = (sparse_item_userF*alpha).astype('double')
train_drink = (sparse_item_userD*alpha).astype('double')

foodModel.fit(train_food)

drinkModel.fit(train_drink)

sparse_item_userF.toarray()

userNumber = 121
#User 343 - Both(F&B), 121 - Both(F&B)

recommendedFood = foodModel.recommend(userNumber, sparse_item_userF[userNumber])
print(recommendedFood)
recommendArray = np.asarray(recommendedFood)
recommendation, scores = np.split(recommendArray, 2)
recommendation = recommendation.flatten().astype(int)
scores = scores.flatten().astype(float)

reccoFood = pd.DataFrame()

ReferenceIDs = organizedLIData[["item_id", "item_name"]].drop_duplicates(keep = 'first')
for id in recommendation:
  reccoFood = reccoFood.append(ReferenceIDs[ReferenceIDs.item_id == id], ignore_index = True)

reccoFood['Score'] = scores.tolist()

#Displays Item Name and Accuracy
print("Top 3 Food Recommendations for User #" + str(userNumber) + ": \n")
print(reccoFood.loc[0:3])

print(recommendedFood)

recommendedDrink = drinkModel.recommend(userNumber, sparse_item_userF[userNumber])

recommendArray = np.asarray(recommendedDrink)
recommendation, scores = np.split(recommendArray, 2)
recommendation = recommendation.flatten().astype(int)
scores = scores.flatten().astype(float)

reccoDrink = pd.DataFrame()

ReferenceIDs = organizedLIData[["item_id", "item_name"]].drop_duplicates(keep = 'first')
for id in recommendation:
  reccoDrink = reccoDrink.append(ReferenceIDs[ReferenceIDs.item_id == id], ignore_index = True)

reccoDrink['Score'] = scores.tolist()

#Displays Item Name and Accuracy
print("Top 3 Drink Recommendations for User #" + str(userNumber) + ": \n")
print(reccoDrink.loc[0:3])