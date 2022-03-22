"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

import os
import math
from datetime import datetime
import pandas as pd
import tda
from tda import auth
from tda.orders.common import OrderType, PriceLinkBasis, PriceLinkType, StopPriceLinkType, first_triggers_second, one_cancels_other
from tda.orders.options import option_buy_to_open_limit, option_sell_to_close_limit, option_sell_to_close_market
from . import config
from tda.orders.common import Duration, Session
from tda.orders.common import OrderType


####################################                AUTHENTICATE                 ####################################

def login():
    """Login to TDA"""
    token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ameritrade_credentials.json')
    api_key = config.api_key
    redirect_uri = config.redirect_uri
    try:
        c = auth.client_from_token_file(token_path, api_key)
    except FileNotFoundError:
        from selenium import webdriver
        with webdriver.Chrome(r'C:\Users\Owner\Desktop\Projects\ec2-tda-autobot\fastapilib\chromedriver.exe') as driver:
            c = auth.client_from_login_flow(
            driver, api_key, redirect_uri, token_path)
    #print(token_path)
    return c


####################################              GET OPTION CHAIN               ####################################

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
        #print("Options Chain:", options_df)
        return options_df


####################################             GET OPTION STRIKES              ####################################

def get_strikes(df, strike, dte):
    """Get strike closest to underlying price"""
    # Sort df by DTE
    df = df[(df['daysToExpiration'] <= dte)]
    #Sort df by strike
    df =df.iloc[(df['strikePrice'] - strike).abs().argsort()[:1]]
    df.reset_index(drop=True, inplace=True)
    strike_price = df['strikePrice'][0]
    print("Strike:", strike_price)
    return strike_price


####################################              Truncation Func.               ####################################

def truncate(number, decimals=0):
    """Returns a value truncated to a specific number of decimal places.    """
    if not isinstance(decimals, int):
        raise TypeError("decimal places must be an integer.")
    elif decimals < 0:
        raise ValueError("decimal places has to be 0 or more.")
    elif decimals == 0:
        return math.trunc(number)

    factor = 10.0 ** decimals
    return math.trunc(number * factor) / factor


####################################             FILTER OPTION CHAIN             ####################################

def filter_options(symbol, option_df, strike_price, putcall, dte):
    """Filter options to standards"""
    ## Add variables here or in webhook##
        #t = '2021-12-05'
        #expiry_date = custom_expiry_date(t)  # Convert string date to expiry timestamp
        #dte = 0
    # Apply filters
    filtered_df = option_df[(option_df['daysToExpiration'] <= dte) &    # DTE range
                            (option_df['strikePrice'] == strike_price)]  # Specific Strike Price
    filtered_df.reset_index(inplace=True, drop=True)
    filtered_df = (filtered_df.loc[filtered_df['daysToExpiration'].idxmax()]).to_frame().transpose().reset_index(drop=True)
    print("Filters:", symbol, putcall, strike_price, "Days to Expiry:", filtered_df['daysToExpiration'][0])
    #print("filtered Chain:", filtered_df)
    return filtered_df


####################################             CREATE/PLACE ORDER              ####################################

def create_buy_order(c, quantity, filtered_df):
    """Create Order"""
    symbol = filtered_df['symbol'].item()
    ## Used price variable when order is limit and not market below
    # price = Whatever code you want to use here to set your slippage
    price = truncate(((filtered_df['bid']+filtered_df['ask'])/2).item(),2)
    # Take profit percentage "OCO leg #1, limit order"
    tp_price = truncate(price + (price * .40), 2)
    # Trailing stop offset
    #trailing_stop_price = 10
    # Stop loss percentage "OCO leg #2, limit order"
    sl_price = truncate(price - (price * .20), 2)
    # Stop loss activation price for "stop-limit orders"
    stop_price = truncate(price - (price * .18), 2)
    print("Create BUY TO OPEN Order:", symbol, quantity, price)
    print("TP:", tp_price, "SL/ST:", sl_price, stop_price)
    #time.sleep(3)
    try:
        spec = first_triggers_second(
            option_buy_to_open_limit(symbol, quantity, price),
                one_cancels_other(option_sell_to_close_limit(symbol, quantity, tp_price)
                                  .set_duration(tda.orders.common.Duration.GOOD_TILL_CANCEL),
                                  option_sell_to_close_limit(symbol, quantity, sl_price)
                                    .set_order_type(OrderType.STOP_LIMIT)
                                    .set_stop_price(stop_price)
                                    .set_duration(tda.orders.common.Duration.GOOD_TILL_CANCEL)
                                    ))

        res =  c.place_order(config.account_id, spec)
        # shows tda build spec location
        print(spec)
        # HTTP status Code
        print("Status:", res.status_code, "--->", datetime.now())
        try:
            # Actual TDA response. Not applicable to every order
            print(res.json())
        except:
            pass
        status = 'Buy order placed'
    except Exception as exc:
        print(f'exception in option_order: {str(exc)}')
        status = 'error: '+str(Exception)
    return status

####################################         PASS WEBHOOK TO FUNCTIONS           ####################################

def main(webhook_message):
    """Execute Functions"""
    ## Copy/paste into tv alert body. Adjust quantity and dte. Match password to main.py##
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
        # Comes in as a dict
        print(type(webhook_message))
        u_price = webhook_message.close
        quantity = webhook_message.quantity
        uticker = webhook_message.ticker
        instruction = webhook_message.instruction
        putcall = webhook_message.callput
        dte = webhook_message.dte

        c = login()
        if instruction == "BUY_TO_OPEN":
            options_df = options_chain(c, uticker, putcall) # get options chain
            print("option_df:", options_df.head) # display option_df
            strike_price = get_strikes(options_df, u_price, dte)
            #strike_price = custom_round(u_price, 0.5) # get current ATM strike
            filtered_df = filter_options(uticker, options_df, strike_price, putcall, dte)    # filter options chain
            print("filtered_df:",filtered_df) # display filtered_df
            status = create_buy_order(c, quantity, filtered_df) # place order
        # time.sleep(5)
        print("confirm:", status)
        return 'Make It Rain!'
    except Exception as exc:
        print(f'Error in main: {str(exc)}')