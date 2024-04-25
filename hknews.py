# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 10:13:20 2024

@author: Bogdan Tudose
@email: bogdan.tudose@trainingthestreet.com

"""
#https://www3.hkexnews.hk/sdw/search/searchsdw.aspx
#09988, 01211, 00005, 9989, 1215, 

#%% Import Packages
from selenium import webdriver
import pandas as pd
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
#%% Open Website w Selenium
url = "https://www3.hkexnews.hk/sdw/search/searchsdw.aspx"

driver = webdriver.Chrome('C:\webdrivers\chromedriver.exe')
driver.maximize_window()
driver.get(url)
#%% Web Elements:
        #date: input name txtShareholdingDate
        #stock code: input name txtStockCode
        #search btn: id = btnSearch
#%% Convert to table
html=driver.page_source
soup=BeautifulSoup(html,'html.parser')
text = str(soup.html)
tables=pd.read_html(text)
df = tables[0]

for col in df.columns:
    print(col)
    df[col] = df[col].apply(lambda x: x.split(": ")[-1])

df['Shareholding'] = pd.to_numeric(df['Shareholding'].str.replace(',',''))
col = '% of the total number of Issued Shares/ Warrants/ Units'
df[col] = pd.to_numeric(df[col].str.replace('%',''))

#%% Function to grab data
def grabDataHKE(ticker, date):
    #Interact with website
    dateBox = driver.find_elements(By.NAME, 'txtShareholdingDate')[0]
    driver.execute_script(f"arguments[0].value = '{date}';", dateBox)

    stockBox = driver.find_elements(By.NAME, 'txtStockCode')[0]
    stockBox.clear() #clear old text if any
    stockBox.send_keys(ticker) #enter new ticker

    searchBtn = driver.find_elements(By.ID, 'btnSearch')[0]
    searchBtn.click() 
    
    #Grab and clean table
    html=driver.page_source
    soup=BeautifulSoup(html,'html.parser')
    tables=pd.read_html(str(soup.html))
    df = tables[0]
    
    #Clean table
    for col in df.columns:
        # print(col)
        df[col] = df[col].apply(lambda x: x.split(": ")[-1])

    df['Shareholding'] = pd.to_numeric(df['Shareholding'].str.replace(',',''))
    col = '% of the total number of Issued Shares/ Warrants/ Units'
    df[col] = pd.to_numeric(df[col].str.replace('%',''))

    #output table
    return df
    

#%% Loop
stocks = ['09988', '01211', '00005', '09989', '01215','09666','03690']
dates =  ['2023/03/06','2023/03/07']

dataMap = {}
# ticker = stocks[1]
for ticker in stocks:
    dataMap[ticker] = {}
    for date in dates:
        print(ticker, date)
        df = grabDataHKE(ticker, date)
        dataMap[ticker][date] = df

#%% Deltas
deltas = {}
for ticker in dataMap.keys():
    date1 = dates[0]
    date2 = dates[1]
    df1 = dataMap[ticker][date1]
    df2 = dataMap[ticker][date2]
    merged = df1.merge(df2,how='outer', on=list(df1.columns[0:3]), suffixes=("_old", "_new"))
    merged['Delta'] = merged['Shareholding_new'] - merged['Shareholding_old']
    merged = merged.sort_values('Delta',ascending=False)
    deltas[ticker] = merged
    print(ticker, f"Largest delta: {merged.iloc[0]['Delta']:,.0f} from {merged.iloc[0,1]}")
    
#%% Export all data
with pd.ExcelWriter('Output/hkex.xlsx') as writer:
    
    for ticker in deltas.keys():
        saveDF = deltas[ticker]
        saveDF.to_excel(writer, sheet_name=ticker, index=False)
