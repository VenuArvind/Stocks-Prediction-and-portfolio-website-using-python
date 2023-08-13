import requests
from lxml import etree
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import pymongo

uri='mongodb+srv://arvind19rajan:Venu2002@test1.zs9ohef.mongodb.net/?retryWrites=true&w=majority'
myclient = pymongo.MongoClient(uri)
mydb = myclient["adb_project"]
mycollection=mydb['historical']

ids = list()
ids.append('GOOGL')
ids.append('AAPL')
ids.append('MSFT')
ids.append('TSLA')
ids.append('NVDA')
ids.append('META')
ids.append('NFLX')
ids.append('KO')
ids.append('MCD')
ids.append('CSCO')


def scrape_data(stock):
    url = f'https://finance.yahoo.com/quote/{stock}/history?p={stock}'
    driver = webdriver.Chrome(executable_path=r'/opt/homebrew/bin/chromedriver')
    driver.get(url)
    time.sleep(1)
    html = driver.page_source
    r = requests.get(url)
    web_content = BeautifulSoup(html, 'html.parser')
    dom = etree.HTML(str(web_content))
    for i in range(1, 101):
        web_date = dom.xpath(
            "//*[@id='Col1-1-HistoricalDataTable-Proxy']/section/div[2]/table/tbody/tr["+str(i)+"]/td[1]/span")[0].text
        web_price = dom.xpath(
            "//*[@id='Col1-1-HistoricalDataTable-Proxy']/section/div[2]/table/tbody/tr["+str(i)+"]/td[2]/span")[0].text
        if web_price == 'Dividend':
            return
        stock = str(stock)
        obj1={
            "Name":stock,
            "Price":web_price,
            "Date":web_date
        }
        x = mycollection.insert_one(obj1)
        print(obj1)
    return


for id in ids:
    scrape_data(id)


