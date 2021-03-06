"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

from tda import auth
import tda
import os
import json
from fastapi import FastAPI
from pydantic import BaseModel
from fastapilib import config, trade, oco
import traceback
import time


class webhook_message(BaseModel):
        ticker: str
        close: float
        quantity: float
        dte: float
        callput: str
        instruction: str
        passphrase: str


app = FastAPI()

start = time.time()

token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'fastapilib/ameritrade_credentials.json')
api_key = config.api_key
c = auth.client_from_token_file(token_path, api_key)



@app.get('/quote/{symbol}')
def quote(symbol):
    response = c.get_quote(symbol)

    #print(json.dumps(response.json(), indent=4))
    return response.json()


@app.get('/option/chain/{symbol}')
def option_chain(symbol):
    response = c.get_option_chain(symbol)

    #print(json.dumps(response.json(), indent=4))
    return response.json()


@app.get('/positions')
def positions():
    fields = c.Account.Fields('positions')
    response = c.get_account(config.account_id, fields = fields)

    print(response.json())
    return response.json()

    # fields = c.Account.Fields('orders')
    # response = c.get_account(config.account_id, fields = fields)

    # print(json.load(response))
    # return response.json()


@app.post('/option/order')
def option_order(webhook_message: webhook_message):
    print("Webhook Recieved:", webhook_message.dict())
    ##have not been able to test 1st if statement##
    if webhook_message.passphrase not in webhook_message.passphrase:
            return {
            "status": "fail",
            "code": "401",
            "message": "Unauthorized, no passphrase"
        }
    if webhook_message.passphrase != config.webhook_passphrase:
        return {
            "status": "fail",
            "code": "401",
            "message": "Invalid passphrase"
        }
    try:
        trading_params = trade.main(webhook_message) # Add this line to push to trade,py.
        traceback.print_exc()
        return {
            "status": "success",
            "code": "200",
            "message": f"{str(trading_params)}"
        }
    except Exception as exc:
        traceback.print_exc()
        print(f'exception in option_order: {str(exc)}')
        return {
            "status": "error",
            "code": "500",
            "message": f"{str(Exception)}"
        }




@app.post('/test')
def option_order(webhook_message: webhook_message):
    print("Webhook Recieved:", webhook_message.dict())
            ##have not been able to test 1st if statement##
    if webhook_message.passphrase not in webhook_message.passphrase:
            return {
            "status": "fail",
            "code": "401",
            "message": "Unauthorized, no passphrase"
        }
    if webhook_message.passphrase != config.webhook_passphrase:
        return {
            "status": "fail",
            "code": "401",
            "message": "Invalid passphrase"
        }
    try:
        trading_params = oco.main(webhook_message) # Add this line to push to oco.py.
        traceback.print_exc()
        return {
            "status": "success",
            "code": "200",
            "message": f"{str(trading_params)}"
        }
    except Exception as exc:
        traceback.print_exc()
        print(f'exception in option_order: {str(exc)}')
        return {
            "status": "error",
            "code": "500",
            "message": f"{str(Exception)}"
        }



app_runtime = time.time() - start
print("main.py runtime:", app_runtime)
