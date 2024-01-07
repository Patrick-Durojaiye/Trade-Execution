import requests
import pandas as pd
import numpy as np
import time
import base64
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from dotenv import load_dotenv
import os

base_url_1 = "https://api.binance.com/"


def get_order_book_data(symbol, limit):
    """

    Args:
        symbol (str): Market Symbol e.g. BTCUSDT
        limit (float): Amount of Data to Fetch

    Returns:
        pandas Dataframe: Dataframe for bids and asks
    """
    url = base_url_1 + "api/v3/depth"
    params = {"symbol": symbol, "limit": limit}

    # Fetches market order book data
    try:
        response = requests.get(url=url, params=params)
    except requests.exceptions.HTTPError as error:
        # should be changed to log
        print("Http Error:", error)
    except requests.exceptions.ConnectionError as error:
        print("Connection Error:", error)
    except requests.exceptions.Timeout as error:
        print("Timeout Error:", error)
    except requests.exceptions.RequestException as error:
        print("Request Exception", error)

    order_book = response.json()

    bids = pd.DataFrame(order_book["bids"], columns=["price", "quantity"], dtype=float)
    asks = pd.DataFrame(order_book["asks"], columns=["price", "quantity"], dtype=float)

    return bids, asks


def measure_liquidity(bids, asks, mid_price_depth_range):
    """
    If asset is highly illiquid, one should have a large mid_price_depth_range value

    Args:
        bids (Dataframe): market bids
        asks (Dataframe): market asks
        mid_price_depth_range (Float): market depth range %

    Returns:
        float: Liquidity for market
    """

    mid_price = (bids["price"].iloc[0] + asks["price"].iloc[0]) / 2

    spread = asks["price"].iloc[0] - bids["price"].iloc[0]

    depth_threshold = mid_price * mid_price_depth_range
    bids_depth = bids[bids["price"] >= mid_price - depth_threshold]["quantity"].sum()
    asks_depth = asks[asks["price"] <= mid_price + depth_threshold]["quantity"].sum()
    order_book_depth = bids_depth + asks_depth

    liquidity = order_book_depth / spread if spread > 0 else 0
    return liquidity


def get_price(symbol):
    """
    Gets price for market

    Args:
        symbol (str): Market Symbol e.g. BTCUSDT

    Returns:
        float: Price for the market
    """
    url = base_url_1 + "api/v3/ticker/price"
    params = {"symbol": symbol}

    try:
        response = requests.get(url=url, params=params)
    except requests.exceptions.HTTPError as error:
        # should be changed to log
        print("Http Error:", error)
    except requests.exceptions.ConnectionError as error:
        print("Connection Error:", error)
    except requests.exceptions.Timeout as error:
        print("Timeout Error:", error)
    except requests.exceptions.RequestException as error:
        print("Request Exception", error)

    ticker_data = response.json()

    return ticker_data["price"]


def get_tick_size(symbol):
    """
    Gets Tick Size for Market
    Args:
        symbol (str): Market Symbol e.g. BTCUSDT

    Returns:
        float: tick size
    """

    url = base_url_1 + "api/v3/exchangeInfo"

    params = {
        "symbol": symbol,
    }

    try:
        response = requests.get(url=url, params=params)
    except requests.exceptions.HTTPError as error:
        # should be changed to log
        print("Http Error:", error)
    except requests.exceptions.ConnectionError as error:
        print("Connection Error:", error)
    except requests.exceptions.Timeout as error:
        print("Timeout Error:", error)
    except requests.exceptions.RequestException as error:
        print("Request Exception", error)

    ticker_data = response.json()
    return ticker_data["symbols"][0]["filters"][0]["tickSize"]


def aggre(symbol, current_time):
    """
    Gets Aggregated Trades for the past hour
    Args:
        symbol: Market Symbol e.g. BTCUSDT
        current_time: Current Timestamp

    Returns:
        ndarray: Timestamps of Buy and Sell Trades in a Numpy Array
    """

    url = base_url_1 + "api/v3/aggTrades"

    time_one_hour_ago = current_time - (1 * 60 * 60 * 1000)
    params = {
        "symbol": symbol,
        "limit": 1000,
        "startTime": time_one_hour_ago,
        "endTime": current_time,
    }

    try:
        response = requests.get(url=url, params=params)
    except requests.exceptions.HTTPError as error:
        # should be changed to log
        print("Http Error:", error)
    except requests.exceptions.ConnectionError as error:
        print("Connection Error:", error)
    except requests.exceptions.Timeout as error:
        print("Timeout Error:", error)
    except requests.exceptions.RequestException as error:
        print("Request Exception", error)

    trades = response.json()

    buy_timestamps_lst = []
    sell_timestamps_lst = []

    for trade in trades:
        # Is a buy trade
        if not trade["m"]:
            buy_timestamps_lst.append(float(trade["T"]))

        # Is a sell trade
        elif trade["m"]:
            sell_timestamps_lst.append(float(trade["T"]))

    buy_timestamps_arr = np.array(buy_timestamps_lst)
    sell_timestamps_arr = np.array(sell_timestamps_lst)

    return buy_timestamps_arr, sell_timestamps_arr


def order(symbol, order_type, size):
    """
    Submits buy or sell market order
    Args:
        symbol (str): Market Symbol e.g. BTCUSDT
        order_type (int): Denotes if buy or sell order, +1 for buy and -1 for sell
        size (float): Total Quantity for order

    Returns:
        boolean
    """

    load_dotenv()
    API_KEY = os.getenv("API_KEY")
    PRIVATE_KEY_PATH = "test-prv-key.pem"  # Replace with your file path

    with open(PRIVATE_KEY_PATH, 'rb') as f:
        private_key = load_pem_private_key(data=f.read(),
                                           password=None)
    url = base_url_1 + "api/v3/order"

    if order_type == 1:
        side = "BUY"
    elif order_type == -1:
        side = "SELL"

    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": size,
    }

    # Timestamp the request
    timestamp = int(time.time() * 1000)
    params['timestamp'] = timestamp

    # Sign the request
    payload = '&'.join([f'{param}={value}' for param, value in params.items()])
    signature = base64.b64encode(private_key.sign(payload.encode('ASCII')))
    params['signature'] = signature

    # Send request
    headers = {
        'X-MBX-APIKEY': API_KEY,
    }

    try:
        response = requests.post(url=url, headers=headers, data=params)
    except requests.exceptions.HTTPError as error:
        # should be changed to log
        print("Http Error:", error)
    except requests.exceptions.ConnectionError as error:
        print("Connection Error:", error)
    except requests.exceptions.Timeout as error:
        print("Timeout Error:", error)
    except requests.exceptions.RequestException as error:
        print("Request Exception", error)

    return True
