"""--------------------------------------------------------------------------------------------------------------------
Copyright 2022 Kyle Jorgensen
Licensed under the Apache License, Version 2.0
THIS CODE IS PROVIDED AS IS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND
This file is part of the Open Source Library (www.github.com/KJJorgensen)
--------------------------------------------------------------------------------------------------------------------"""

from ..fastapilib import trade

data = {'ticker': 'RCL', 'close': 68.17, 'quantity': 2, 'dte': 30, 'callput': 'CALL', 'instruction': 'BUY_TO_OPEN', 'passphrase': 'SScamaro98'}

res = trade.main(data)

print(f'result: {res}')