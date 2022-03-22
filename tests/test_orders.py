"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

from tda import auth
import os
import time
import datetime
from dateutil import tz
from ..fastapilib import config
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import json
import pandas as pd

token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ameritrade_credentials.json')
api_key = config.api_key
c = auth.client_from_token_file(token_path, api_key)

engine = create_engine(config.psql, poolclass=QueuePool, pool_size=1, max_overflow=50, pool_recycle=3600,
                           pool_pre_ping=True, isolation_level='AUTOCOMMIT')
def order_details(ztime):
    try:
        fields = c.Account.Fields('orders')
        response = c.get_account(config.account_id, fields = fields)
        r = json.load(response)
        #print(r)
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
        #print(pos[order_id])
        print("Entered to db:", usymbol_value, effect_value, opt_symbol, quantity, status)
        if pos is not None:
            orders_df = pd.DataFrame(pos).T.reset_index() # start index at 0
            orders_df.columns = ['order_id', 'datetime', 'underlying', 'effect', 'symbol', 'quantity', 'status']
            orders_df.to_sql('orders', engine, if_exists='append', index=False, method='multi')
    except KeyError as e:
        if e.args[0] ==  'orderStrategies':
            print("No Orders")
    return None

ztime = datetime.datetime.utcnow().replace(tzinfo=tz.UTC)
time.sleep(2)
order_details(ztime)