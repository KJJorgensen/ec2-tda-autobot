"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

import datetime
from dateutil import tz
import os
import time
import traceback
import json
import math
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import tda
from pytz import timezone
from tda import auth
from . import config

start = time.time()


engine = create_engine(config.psql, poolclass=QueuePool, pool_size=1, max_overflow=50, pool_recycle=3600,
                           pool_pre_ping=True, isolation_level='AUTOCOMMIT')# postgres db

# Authentication
def login():
    """Login to TDA"""
    token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ameritrade_credentials.json')
    api_key = config.api_key
    redirect_uri = config.redirect_uri
    try:
        c = auth.client_from_token_file(token_path, api_key)
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome(r'C:\Users\Owner\Desktop\Projects\tda-autobot\chalicelib\chromedriver.exe') as driver:
            c = auth.client_from_login_flow(
            driver, api_key, redirect_uri, token_path)
    #print(token_path)
    traceback.print_exc()
    return c


def options_chain(c, symbol,putcall):
    """Get options chain"""
    options_dict = []
    r = c.get_option_chain(symbol)
    query = r.json()
    # Flatten nested JSON
    for contr_type in ['callExpDateMap', 'putExpDateMap']:
        contract = dict(query)[contr_type]
        expirations = contract.keys()
        for expiry in list(expirations):
            strikes = contract[expiry].keys()
            for st in list(strikes):
                entry = contract[expiry][st][0]
                # Create list of dictionaries with the flattened JSON
                options_dict.append(entry)
    # Check if list is empty
    if options_dict:
        # Remove any unknown keys from response (in case TDA changes the API response without warning)
        key_count = len(options_dict[0].keys())
        if key_count > 49:
            # List of known keys
            keys = ["putCall", "symbol", "description", "exchangeName", "bid", "ask", "last", "mark", "bidSize"
                    "askSize", "bidAskSize", "lastSize", "highPrice", "lowPrice", "openPrice", "closePrice",
                    "totalVolume", "tradeDate", "tradeTimeInLong", "quoteTimeInLong", "netChange", "volatility", "delta",
                    "gamma", "theta", "vega", "rho", "openInterest", "timeValue", "theoreticalOptionValue",
                    "theoreticalVolatility", "optionDeliverablesList", "strikePrice", "expirationDate",
                    "daysToExpiration", "expirationType", "lastTradingDay", "multiplier", "settlementType",
                    "deliverableNote", "isIndexOption", "percentChange", "markChange", "markPercentChange",
                    "nonStandard", "inTheMoney", "mini", "intrinsicValue", "pennyPilot"]
            # Drop unknown keys
            options_dict = [{k: single[k] for k in keys if k in single} for single in options_dict]
    # Convert dictionary to dataframe
        options_df = pd.DataFrame(options_dict)
        options_df = options_df[(options_df['putCall'] == putcall)]  # Call or Put
        return options_df


def get_strikes(df, strike, dte):
    df = df[(df['daysToExpiration'] <= dte)]   # DTE range
    df =df.iloc[(df['strikePrice'] - strike).abs().argsort()[:1]]
    df.reset_index(drop=True, inplace=True)
    strike_price = df['strikePrice'][0]
    return strike_price


# def custom_round(x, base=0.5):
#     """Round to strikes"""
#     if np.isnan(x):
#         x = 0
#     rounded = base * round(float(x) / base)
#     return rounded


# def custom_expiry_date(t):
#     """Convert string time to expiry time"""
#     t = t + ' 20:00:00'
#     expiry_datetime = datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
#     expiry_datetime = timezone('UTC').localize(expiry_datetime)
#     expiry_timestamp = int(datetime.datetime.timestamp(expiry_datetime)) * 1000
#     return expiry_timestamp


def filter_options(symbol, option_df, strike_price, putcall, dte):
    """Filter options to standards"""
    ## Add filters here or in webhook##
    #t = '2021-12-05'
    #expiry_date = custom_expiry_date(t)  # Convert string date to expiry timestamp
    #dte = 0
    # Apply filters
    filtered_df = option_df[(option_df['daysToExpiration'] <= dte) &    # DTE range
                            (option_df['strikePrice'] == strike_price)]  # Specific Strike Price
    filtered_df.reset_index(inplace=True, drop=True)
    filtered_df = (filtered_df.loc[filtered_df['daysToExpiration'].idxmax()]).to_frame().transpose().reset_index(drop=True)
    print("Filters:", symbol, putcall, strike_price, "Days to Expiry:", filtered_df['daysToExpiration'][0])
    return filtered_df

#(option_df['putCall'] == putcall) &  # Call or Put
# (option_df['daysToExpiration'] >= 3) &    # DTE cutoff

def create_buy_order(c, quantity, filtered_df):
    """Create orders"""
    symbol = filtered_df['symbol'].item()
    ## Used price when order is limit and not market below
    price = ((filtered_df['bid']+filtered_df['ask'])/2).item() # Whatever code you want to use here to set your slippage
    print("Create BUY TO OPEN Order:", symbol, quantity, price)
    try:
        spec = tda.orders.options.option_buy_to_open_limit(symbol, quantity, price)
        res =  c.place_order(config.account_id, spec)
        print(spec) # shows tda build spec location
        print("Status:", res.status_code) #HTTP Code
        try:
            print(res.json()) # actual TDA response
        except:
            pass
        status = 'buy order placed'
    except Exception as exc:
        print(f'exception in option_order: {str(exc)}')
        status = 'error: '+str(Exception)
    return status

def create_sell_order(c, symbol, quantity, price):
    """Create orders"""
    print("Create SELL TO CLOSE Order:", symbol, quantity, price)
    try:
        spec = tda.orders.options.option_sell_to_close_limit(symbol, quantity, price)
        res = c.place_order(config.account_id, spec)
        print(spec) # shows tda build spec location
        print(res.status_code)
        try:
            print(res.json()) # actual TDA response
        except:
            pass
        status = 'sell order placed'
    except Exception as exc:
        print(f'exception in option_order: {str(exc)}')
        status = 'error: '+str(Exception)
    return status

def get_positions(c):
    fields = c.Account.Fields('positions')
    response = c.get_account(config.account_id, fields = fields)
    r = json.load(response)
    pos_dict = {}
    for i in r['securitiesAccount']['positions']:
        symbol = i['instrument']['underlyingSymbol']
        opt_symbol = i['instrument']['symbol']
        close_quantity = i['settledLongQuantity'] + i['settledShortQuantity']
        pos_dict[symbol] = [opt_symbol, close_quantity]
    print("Find Open Position:", pos_dict)
    return pos_dict

def get_sell_price(c, symbol):
    r = c.get_quote(symbol).json()
    slip = ((r[symbol]['bidPrice'] + r[symbol]["askPrice"])/2)
    price = math.ceil(slip*100)/100 # Whatever code you want to use here to set your slippage
    return price

def order_details(c, ztime):
    try:
        ztime = ztime - datetime.timedelta(seconds =  1)
        fields = c.Account.Fields('orders')
        response = c.get_account(config.account_id, fields = fields)
        r = json.load(response)
        pos = {}
        for order_strat in r["securitiesAccount"]['orderStrategies']:
            order_time = datetime.datetime.strptime(order_strat['enteredTime'], '%Y-%m-%dT%H:%M:%S+0000').replace(tzinfo=tz.UTC)
            if order_time >= ztime:
                status = order_strat['status']
                order_id = order_strat['orderId']
                time_value = order_time
                quantity = order_strat["quantity"]
                for legs in order_strat['orderLegCollection']:
                    effect_value = legs['positionEffect']
                    inst = legs['instrument']
                    opt_symbol = inst['symbol']
                    usymbol_value = inst['underlyingSymbol']
                    pos[order_id] = [time_value, usymbol_value, effect_value, opt_symbol, quantity, status]
        if pos is not None:
            orders_df = pd.DataFrame(pos).T.reset_index() # start index at 0
            orders_df.columns = ['order_id', 'datetime', 'underlying', 'effect', 'symbol', 'quantity', 'status']
            print(orders_df)
            orders_df.to_sql('orders', engine, if_exists='append', index=False, method='multi')
    except KeyError as e:
        if e.args[0] ==  'orderStrategies':
            print("No Orders")
    return None

def main(webhook_message):
##copy/paste into tv alert body. adjust quantity and dte. match password to main.py##
    """ Webhook_message format:
    {
    "ticker": "{{ticker}}",
    "close": {{close}},
    "quantity": 1,
    "dte": 1,
    "callput": "{{strategy.order.alert_message}}",
    "instruction": "{{strategy.order.comment}}",
    "passphrase": "xxxxxxxxx"
    }"""

    try:
        print(type(webhook_message))  # comes in as a dict
        u_price = webhook_message.close
        quantity = webhook_message.quantity
        uticker = webhook_message.ticker
        instruction = webhook_message.instruction
        putcall = webhook_message.callput
        dte = webhook_message.dte

        c = login() # login
        if instruction == "BUY_TO_OPEN":
            options_df = options_chain(c, uticker, putcall) # get options chain
            print("option_df:", options_df.head) # display option_df
            strike_price = get_strikes(options_df, u_price, dte)
            #strike_price = custom_round(u_price, 0.5) # get current ATM strike
            filtered_df = filter_options(uticker, options_df, strike_price, putcall, dte)    # filter options chain
            print("filtered_df:",filtered_df) # display filtered_df
            ztime = datetime.datetime.utcnow().replace(tzinfo=tz.UTC)
            status = create_buy_order(c, quantity, filtered_df) # place order
            order_details(c, ztime) # add to db

        elif instruction == "SELL_TO_CLOSE":
            pos_dict = get_positions(c)
            if uticker in pos_dict:
                symbol = pos_dict[uticker][0]
                quantity = pos_dict[uticker][1]
                price = get_sell_price(c, symbol)
                ztime = datetime.datetime.utcnow().replace(tzinfo=tz.UTC)
                status = create_sell_order(c, symbol, quantity, price) # place order
                order_details(c, ztime) # add to db
        # time.sleep(5)
        # print("confirm:",status)
        return 'Make It Rain!'
    except Exception as exc:
        traceback.print_exc()
        print(f'Error in main: {str(exc)}')


trade_runtime = (time.time() - start)
print("trade.py runtime:", trade_runtime)
