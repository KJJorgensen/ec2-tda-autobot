# TDA-Autobot

TDA-Autobot is an automated fire and forget trading mechanism
utilizing Alex Golec's(Author) tda-api wrapper, Tradingview webhook alerts, and AWS EC2 for cloud hosting.

NEW!!! Automate creating your EC2 Instance to host TDA-Autobot in the cloud @ https://github.com/MarketMakerLite/AWS

The code itself is universal in the fact that it has no idea what ticker, time frame of chart, or strategy is being used in Tradingview to issue the alert. Rather, its purpose is to take any incoming alert and place an order to TD-Ameritrade. All this via a serverless (cloud) configuration.

To perform this operation, the code runs the following processes:

-   Authenticates with TD-Ameritrade API.
-   Establishes routes and listens for an incoming POST request (Tradingview Webhook).
-   Runs functions and filtering based on details of webhook.
-   Creates order builder spec.
-   Places order through API.

Requires:
-   TDAmeritrade funded Account https://invest.ameritrade.com/
-   TDAmeritrade Developer Account https://developer.tdameritrade.com/home
-   AWS Account https://aws.amazon.com/
-   Tradingview Alert w/ Webhook https://www.tradingview.com/

Test Webhook with Insomnia https://insomnia.rest/download

The webhook message format can be found in the trade.py file for a simple copy and paste to your Tradingview alert body.

I utilized help from several places and only feel it fair to give reference to the information i consumed. So here is a list of useful references:

## Parttimelarry :

https://www.github.com/hackingthemarkets

YouTube Tutorial Video for this repo:
https://www.youtube.com/watch?v=-wT9h9Nc9sk

YouTube Channel (for TD Ameritrade API):
https://youtube.com/parttimelarry

## Alex Golec tda-api wrapper :

https://github.com/alexgolec/tda-api.git

https://tda-api.readthedocs.io/en/latest/index.html

https://discord.com/invite/Ddha8cm6dx

## Mr. Baker @ MarketMakerLite :

https://marketmakerlite.com (coming soon!)

https://docs.marketmakerlite.com

https://github.com/MarketMakerLite

https://discord.com/channels/837528551028817930/851679862350544926

To Baker and Psslonaki Thank you very much for the help and support!!
