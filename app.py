from flask import Flask, render_template, session, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from pusher import Pusher
from functools import wraps
import requests, json, atexit, time, plotly, plotly.graph_objs as go
import pymongo


app = Flask(__name__)
app.secret_key = b'\x0ex-\xa4%\x1aZ\x86\x17x\xc4\x8e\xe6\xec\xc9\xc5'

# Database
client = pymongo.MongoClient('localhost', 27017)
db = client.cryptofans_users


# Pusher object
pusher = Pusher(
  app_id='1213624',
  key='71b1ee070871ec567e6e',
  secret='7fddc69e517965121436',
  cluster='eu',
  ssl=True
)

# DEMO VARIABLES
demo_eur_value = [0, 0]
demo_owned_currency = {
    "BTC": [0, 0, 0],
    "ETH": [0, 0, 0],
    "XRP":[0, 0, 0],
    "ADA": [0, 0, 0],
    "XLM": [0, 0, 0]
}

# DEMO FUNCTIONS

def show_balance():
    print(" ")
    demo_eur_value[0] = 0
    demo_eur_value[1] = 0
    for currency in demo_owned_currency:
        demo_eur_value[0] = demo_eur_value[0] + demo_owned_currency[currency][1]
        demo_eur_value[1] = demo_eur_value[1] + demo_owned_currency[currency][2]
    print("--------------------------------------------------------------------------------------------------------")
    print("You have invested {} euros and the total value of your portfolio is {}".format (demo_eur_value[0], demo_eur_value[1]))
    print("--------------------------------------------------------------------------------------------------------")
    print(" ")

def show_currencies():
    print(" ")
    print("-------------------------------------------------------------------------------------")
    for currency in demo_owned_currency:
        print("{} : crypto amount - {} , invested amount - {}, current value - {}".format(currency, demo_owned_currency[currency][0], demo_owned_currency[currency][1], demo_owned_currency[currency][2]))
    print("-------------------------------------------------------------------------------------")
    print(" ")

def action_currencies():
    global demo_owned_currency
    print(" ")
    print("-------------------------------")
    print("To buy press 1")
    print("To sell press 2")
    print("-------------------------------")
    user_input = int(input("Your options: "))
    print(" ")
    if user_input == 1:
        print("-------------------------------")
        print("Which currency would you like to buy")
        print("BTC ETH XRP ADA XLM")
        print("-------------------------------")
        user_input = input("Your option: ")
        print(" ")
        print("-------------------------------")
        print("How much would you like to invest?")
        print("-------------------------------")
        user_buy = float(input("Your option: "))
        for currency in demo_owned_currency:
            if user_input in currency:         
                demo_owned_currency[currency][0] = user_buy / float(prices[currency][-1])
                demo_owned_currency[currency][1] = demo_owned_currency[currency][1] + user_buy
                demo_owned_currency[currency][2] = demo_owned_currency[currency][0] * float(prices[currency][-1])
    elif user_input == 2:
        print("-------------------------------")
        print("Which currency would you like to sell")
        print("BTC ETH XRP ADA XLM")
        print("-------------------------------")
        user_input = input("Your option: ")
        print(" ")
        print("-------------------------------")
        print("How much would you like to sell?")
        print("-------------------------------")
        user_sell = float(input("Your option: "))
        for currency in demo_owned_currency:
            if user_input in currency:
                if demo_owned_currency[currency][0] < user_sell:
                    print(" ")
                    print("-------------------")
                    print("Not enough currency")
                    print("-------------------")
                    print(" ")
                else:        
                    demo_owned_currency[currency][0] = demo_owned_currency[currency][0] - user_sell
                    demo_owned_currency[currency][1] = demo_owned_currency[currency][1] - (user_sell * prices[currency])
                    demo_owned_currency[currency][2] = demo_owned_currency[currency][0] * float(prices[currency][-1])



# Variables for currency real time retrieval

total_users = 0

btc_current_price = 0000
eth_current_price = 0000
xrp_current_price = 0000
ada_current_price = 0000
xlm_current_price = 0000

profit_btc = 0000
profit_eth = 0000
profit_xrp = 0000
profit_ada = 0000
profit_xlm = 0000

times = []
currencies = ["BTC", "ETH", "XRP", "ADA", "XLM"]
currencies_1 = ["BTC"]
currencies_2 = ["ETH"]
currencies_3 = ["XRP", "ADA", "XLM"]
prices = {"BTC": [ ],
          "ETH": [ ],
          "XRP": [ ],
          "ADA": [ ],
          "XLM": [ ]
}

# Decorators
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    
    return wrap

# Routes
from user import routes

@app.route("/")
def home_page():
    return render_template("home.html")

@app.route("/login/")
def login_page():
    return render_template("login.html")

@app.route("/signup/")
def signup_page():
    return render_template("signup.html")

@app.route("/about/")
def about_page():
    return render_template("about.html")

@app.route("/dashboard/")
@login_required
def dashboard_page():
    return render_template("dashboard.html", btc_p = btc_current_price, eth_p = eth_current_price, xrp_p = xrp_current_price, ada_p = ada_current_price, xlm_p = xlm_current_price, total_users = total_users, profit_btc= profit_btc, profit_eth = profit_eth, profit_xrp = profit_xrp, profit_xlm = profit_xlm, profit_ada = profit_ada)

@app.route("/charts/")
@login_required
def charts():
    return render_template("charts.html", btc_p = btc_current_price, eth_p = eth_current_price, xrp_p = xrp_current_price, ada_p = ada_current_price, xlm_p = xlm_current_price, total_users = total_users, profit_btc= profit_btc, profit_eth = profit_eth, profit_xrp = profit_xrp, profit_xlm = profit_xlm, profit_ada = profit_ada)

# Function to retrieve the live price of cryptocurrency

def retrieve_data():
    global btc_current_price
    global eth_current_price
    global xrp_current_price
    global ada_current_price
    global xlm_current_price

    global profit_btc
    global profit_eth
    global profit_xrp
    global profit_ada
    global profit_xlm

    # Create a dictionary to save current prices
    current_prices = {}
    for currency in currencies:
        current_prices[currency] = []
    
    # Append the current time to the list of times
    times.append(time.strftime('%H:%M:%S'))

    # Make request to API and get the response as object
    api_url = "https://min-api.cryptocompare.com/data/pricemulti?fsyms={}&tsyms=EUR".format(",".join(currencies))
    response = json.loads(requests.get(api_url).content)

    # Append new price to list of prices for graph
    # Set current price for the bar chart
    for currency in currencies:
        price = response[currency]['EUR']
        current_prices[currency] = price
        prices[currency].append(price)


    # Create an array of traces for graph data
    graph_data_1 = [go.Scatter(
        x = times,
        y = prices.get(currency),
        name = "{} Prices".format(currency)
    ) for currency in currencies_1]

    graph_data_2 = [go.Scatter(
        x = times,
        y = prices.get(currency),
        name = "{} Prices".format(currency)
    ) for currency in currencies_2]

    data = {
        'graph_1': json.dumps(list(graph_data_1), cls=plotly.utils.PlotlyJSONEncoder),
        'graph_2': json.dumps(list(graph_data_2), cls=plotly.utils.PlotlyJSONEncoder)
    }

    if btc_current_price != 0:
         profit_btc = round(-(100 - round((prices["BTC"][-1]*100)/btc_current_price, 4)), 4)
    btc_current_price = prices["BTC"][-1]
    if eth_current_price != 0:
         profit_eth = round(-(100 - round((prices["ETH"][-1]*100)/eth_current_price, 4)), 4)
    eth_current_price = prices["ETH"][-1]
    if xrp_current_price != 0:
         profit_xrp = round(-(100 - round((prices["XRP"][-1]*100)/xrp_current_price, 4)), 4)
    xrp_current_price = prices["XRP"][-1]
    if ada_current_price != 0:
         profit_ada = round(-(100 - round((prices["ADA"][-1]*100)/ada_current_price, 4)), 4)
    ada_current_price = prices["ADA"][-1]
    if xlm_current_price != 0:
         profit_xlm = round(-(100 - round((prices["XLM"][-1]*100)/xlm_current_price, 4)), 4)
    xlm_current_price = prices["XLM"][-1]

    # trigger event
    pusher.trigger("crypto", "data-updated", data)


def demo_scheduler():
    for currency in demo_owned_currency:
        demo_owned_currency[currency][2] = demo_owned_currency[currency][0] * prices[currency][-1]




def db_updater():
    global total_users
    total_users = 0
    for document in db.users.find():
        doc_id = document["_id"]
        total_users = total_users + 1

        new_btc_value = round(document["portfolio"]["BTC"][0] * prices["BTC"][-1], 3)
        new_eth_value = round(document["portfolio"]["ETH"][0] * prices["ETH"][-1], 3)
        new_xrp_value = round(document["portfolio"]["XRP"][0] * prices["XRP"][-1], 3)
        new_ada_value = round(document["portfolio"]["ADA"][0] * prices["ADA"][-1], 3)
        new_xlm_value = round(document["portfolio"]["XLM"][0] * prices["XLM"][-1], 3)

        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.BTC.2": new_btc_value}})
        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.ETH.2": new_eth_value}})
        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.XRP.2": new_xrp_value}})
        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.ADA.2": new_ada_value}})
        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.XLM.2": new_xlm_value}})

        if document["portfolio"]["BTC"][1] !=0:
            profit_btc = round(-(100 - round((document["portfolio"]["BTC"][2]*100)/document["portfolio"]["BTC"][1], 4)), 3)
        if document["portfolio"]["ETH"][1] !=0:
            profit_eth = round(-(100 - round((document["portfolio"]["ETH"][2]*100)/document["portfolio"]["ETH"][1], 4)), 3)
        if document["portfolio"]["XRP"][1] !=0:
            profit_xrp = round(-(100 - round((document["portfolio"]["XRP"][2]*100)/document["portfolio"]["XRP"][1], 4)), 3)
        if document["portfolio"]["ADA"][1] !=0:
            profit_ada = round(-(100 - round((document["portfolio"]["ADA"][2]*100)/document["portfolio"]["ADA"][1], 4)), 3)
        if document["portfolio"]["XLM"][1] !=0:
            profit_xlm = round(-(100 - round((document["portfolio"]["XLM"][2]*100)/document["portfolio"]["XLM"][1], 4)), 3)

        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.BTC.3": profit_btc}})

        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.ETH.3": profit_eth}})

        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.XRP.3": profit_xrp}})

        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.ADA.3": profit_ada}})

        db.users.update_one({"_id": doc_id}, {"$set":{"portfolio.XLM.3": profit_xlm}})

        #Calculate total invested

        total_eur_invested = round(document["portfolio"]["BTC"][1] + document["portfolio"]["ETH"][1] + document["portfolio"]["XRP"][1] + document["portfolio"]["ADA"][1] + document["portfolio"]["XLM"][1], 2)
        db.users.update_one({"_id": doc_id}, {"$set":{"total_value.0": total_eur_invested}})

        total_eur_value = round(document["portfolio"]["BTC"][2] + document["portfolio"]["ETH"][2] + document["portfolio"]["XRP"][2] + document["portfolio"]["ADA"][2] + document["portfolio"]["XLM"][2], 2)
        db.users.update_one({"_id": doc_id}, {"$set":{"total_value.1": total_eur_value}})

        if total_eur_invested !=0:
            profit_eur = round(-(100 - round((total_eur_value*100)/total_eur_invested, 4)), 3)
            db.users.update_one({"_id": doc_id}, {"$set":{"total_value.2": profit_eur}})

# Create schedule for retrieving prices
scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    func=retrieve_data,
    trigger=IntervalTrigger(seconds=8),
    id='prices_retrieval_job',
    name='Retrieve prices every 8 seconds',
    replace_existing=True)
scheduler.add_job(
    func=demo_scheduler,
    trigger=IntervalTrigger(seconds=10),
    id="demo_update",
    name="update the prices ever 10 seconds",
    replace_existing=True)
scheduler.add_job(
    func=db_updater,
    trigger=IntervalTrigger(seconds=9),
    id="db_update",
    name="updates the database every 9 seconds",
    replace_existing=True)


def demo():
    user_input = 0
    while user_input != 5:
        print("-------------DEMO MENU--------------")
        print("To see Euro capital hit 1")
        print("To see owned currency amounts hit 2")
        print("To buy or sell hit 3")
        print("to check current crypto prices hit 4")
        print("To quit the program hit 5")
        print("------------------------------------")
        print(" ")
        user_input = int(input("Your option:"))
        if user_input == 1:
            show_balance()
        elif user_input == 2:
            show_currencies()
        elif user_input == 3:
            action_currencies()
        elif user_input == 4:
                print("------------------------------------------")
                print("BTC value ~ {} €".format(prices["BTC"][-1]))
                print("ETH value ~ {} €".format(prices["ETH"][-1]))
                print("XRP value ~ {} €".format(prices["XRP"][-1]))
                print("ADA value ~ {} €".format(prices["ADA"][-1]))
                print("XLM value ~ {} €".format(prices["XLM"][-1]))
                print("------------------------------------------")
        elif user_input == 5:
            print("Have a great day")

demo()


# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

