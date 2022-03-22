"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

from tda import auth
import os
from ..fastapilib import config
import json

token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'ameritrade_credentials.json')
api_key = config.api_key
c = auth.client_from_token_file(token_path, api_key)


symbol = 'TME_010722P4.5' #add a current position here
r = c.get_quote(symbol).json()
print(r)