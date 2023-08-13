from flask import Flask, session, render_template, url_for, redirect
from flask_wtf import FlaskForm
from wtforms import (StringField, RadioField,  SubmitField)
from lxml import etree
from bs4 import BeautifulSoup
from selenium import webdriver
from wtforms.validators import DataRequired
import pandas as pd
import pymongo
import json
from bson import json_util

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey1'

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["adb_project"]
mycollection=mydb['historical']
mycollection1=mydb['login_data']
mycollection2=mydb['profiles']

def realtime_code(stock):
    url = f'https://finance.yahoo.com/quote/{stock}?p={stock}'
    driver = webdriver.Chrome(
        executable_path=r'/opt/homebrew/bin/chromedriver')
    driver.get(url)
    html = driver.page_source
    web_content = BeautifulSoup(html, "html.parser")
    dom = etree.HTML(str(web_content))
    web_price = dom.xpath(
        "//*[@id='quote-header-info']/div[3]/div[1]/div/fin-streamer[1]")[0].text
    return web_price


def old(stock, date):
    query_entered={
        "Name":stock,
        "Date":date
    }
    mydoc = mycollection.find(query_entered)
    for x in mydoc:
        print(x['Name'],x['Price'],x['Date'])
        return x['Price']

def predict1(stock):
    re = list()
    url = f'https://finance.yahoo.com/quote/{stock}/history?p={stock}'
    driver = webdriver.Chrome(executable_path=r'/opt/homebrew/bin/chromedriver')
    driver.get(url)
    html = driver.page_source
    web_content = BeautifulSoup(html, "html.parser")
    dom = etree.HTML(str(web_content))
    for i in range(1, 101):
        web_price = dom.xpath("//*[@id='Col1-1-HistoricalDataTable-Proxy']/section/div[2]/table/tbody/tr["+str(i)+"]/td[2]/span")[0].text
        if web_price != 'Dividend' and web_price!='Stock Split':
            re.append(web_price)
    numbers_series = pd.Series(re)
    moving_averages = round(numbers_series.ewm(
        span=20, adjust=False).mean(), 2)
    moving_averages_list = moving_averages.tolist()
    return moving_averages_list[-1]


class Infoform(FlaskForm):

    id = StringField('What is the ID of the stock',
                     validators=[DataRequired()])
    time = RadioField('Please choose the type of data', choices=[
                      ('real', 'real-time'), ('old', 'history'), ('predict', 'Predict next day price')])
    date = StringField("Please enter the date like 'Jun 22, 2002'  ")
    submit = SubmitField('Submit')

class LoginForm(FlaskForm):

    uname=StringField('Enter username')
    password=StringField('Enter password')
    submitlogin=SubmitField('Submit')

class ProfileForm(FlaskForm):
    stock_id=StringField('Enter Stock id')
    number=StringField('Enter the number of stocks')
    action = RadioField('Please choose the type of action', choices=[
                      ('add', 'Add new Stock Details'), ('delete', 'Delete Stock Details'), ('update', 'Update Stock Details')])
    submitstock=SubmitField('Submit')


class adminForm(FlaskForm):
    username=StringField('Enter username')
    number=StringField('Enter the password')
    action = RadioField('Please choose the type of action', choices=[
                      ('add', 'Add new User'), ('delete', 'Delete User')])
    submit=SubmitField('Submit')


@app.route('/', methods=['GET', 'POST'])
def index():
    if 'uname' not in session:
        return redirect(url_for('login'))  
    form = Infoform()
    if form.validate_on_submit():
        session['id'] = form.id.data
        session['time'] = form.time.data
        session['date'] = form.date.data
        if session['time'] == 'real':
            session['price'] = realtime_code(session['id'])
        else:
            if session['time'] == 'old':
                session['price'] = old(session['id'], session['date'])
            else:
                if session['time'] == 'predict':
                    session['price'] = predict1(session['id'])
        return redirect(url_for('result'))

    return render_template('index.html', form=form)


@app.route('/result')
def result():
    return render_template('result.html')


@app.route('/login',methods=['GET', 'POST'])
def login():
    form1=LoginForm()
    if form1.validate_on_submit():
        session['uname']=form1.uname.data
        session['password']=form1.password.data
        uname=session['uname']
        password=session['password']
        query={
            "username":uname,
            "password":password
        }
        if uname=='admin' and password=='admin123':
            return redirect(url_for('admin'))
        mydoc1=mycollection1.find(query)
        for x in mydoc1:
            if(x['username']==uname and x['password']==password):
                return redirect(url_for('index'))
            else:
                return redirect(url_for('login'))    
    return render_template('login.html',form1=form1)   


@app.route('/profile',methods=['GET', 'POST'])
def profile():
    form=ProfileForm()
    if form.validate_on_submit():
        id=form.stock_id.data
        number=form.number.data
        action=form.action.data
        if action=='add':
                    obj2={
                        "Name":session['uname'],
                        "id":id,
                        "number":number
                        }
                    x = mycollection2.insert_one(obj2)
                    return redirect(url_for('profile'))
        else:
            if action=='delete':
                obj3={
                    "id":id
                    }
                x=mycollection2.delete_one(obj3)
                return redirect(url_for('profile'))
            
            else:
                if action=='update':
                    obj4={
                        "Name":session['uname'],
                        "id":id
                    }
                    newval={
                        "$set": { "number": number }
                    }
                    mycollection2.update_one(obj4,newval)
                    return redirect(url_for('profile'))
    
    myquery={
        "Name":session['uname']
    }
    mydoc=mycollection2.find(myquery)
    session['results']=json.loads(json_util.dumps(mydoc))
    for x in mydoc:
        print(x['id'],x['number'])
    return render_template('profile.html',form=form,mydoc=mydoc)     

@app.route('/logout')
def logout():
    session.pop('uname',None)  
    session.pop('password',None)  
    return redirect(url_for('login'))

@app.route('/admin',methods=['GET','POST'])
def admin():
    form=adminForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.number.data
        action=form.action.data
        if action=='add':
            obj={
                "username":username,
                "password":password
                }
            x = mycollection1.insert_one(obj)
            return redirect(url_for('admin'))
        else:
            if action=='delete':
                obj3={
                    "username":username
                    }
                x=mycollection1.delete_one(obj3)
                return redirect(url_for('admin'))
                        
    return render_template('admin.html',form=form)

app.run(host='0.0.0.0',debug=True)