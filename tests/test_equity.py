"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

import os
from datetime import datetime
import tda
from tda import auth
from ..fastapilib import config
from tda.orders.equities import equity_buy_limit, equity_sell_limit, equity_buy_market, equity_sell_market, equity_sell_short_limit, equity_buy_to_cover_market
from tda.orders.common import Duration, Session
from tda.orders.common import OrderType
from tda.orders.generic import OrderBuilder



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


def create_buy_order(c):
    """Create Order"""
    price = .8500
    #time.sleep(3)
    try:
        spec = equity_buy_limit('REDU', 1, price)
        OrderBuilder.set_duration(Duration.GOOD_TILL_CANCEL)
        OrderBuilder.set_session(Session.SEAMLESS)

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