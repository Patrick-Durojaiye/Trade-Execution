import numpy as np
from binance_utils import get_price


def linear_impact_function(ct, q):
    """
    Linear Impact function

    Args:
        ct (float): Continuous function that measures order-book liquidity at time t
        q (float): Quantity of asset to be bought/sold

    Returns:
        float: price impact
    """
    return ct * q


def exec_price_one_order(symbol, total_q, theta, order_type, ct, n_integral):
    """
    Average Execution Price for One Order

    Args:
        symbol (str): Market Symbol e.g. BTCUSDT
        total_q (float): Total Quantity for order
        theta (spread): Spread for market of symbol
        order_type (int): Denotes if buy or sell order, +1 for buy and -1 for sell
        ct (float): Liquidity in orderbook
        n_integral: N discrete steps for integral

    Returns:
        float: Execution Price
    """

    # Integration by midpoint rule
    s_t_ = get_price(symbol=symbol)
    delta_v = total_q / n_integral
    v = np.arange(0.5*delta_v, total_q, delta_v)
    integral = np.sum(ct*v)*delta_v
    return s_t_ + ((1 / total_q) * integral) + (order_type * theta / 2)


def avg_exec_price(
    symbol, total_q, theta, order_type, ct, delta, lambda1, lambda2, alpha_self, alpha_cross, beta, n, delta_t,
        n_integral
):
    """
    Average Execution Price for N Orders

    Args:
        symbol (str): Market Symbol e.g. BTCUSDT
        total_q (float): Total Quantity for order
        theta (spread): Spread for market of symbol
        order_type (int): Denotes if buy or sell order, +1 for buy and -1 for sell
        ct (float): Liquidity in orderbook
        delta (float): Tick Size
        lambda1 (float): Intensity for buy orders
        lambda2 (float): Intensity for sell orders
        alpha_self (float): Self-Excitation parameter
        alpha_cross (float): Cross-Excitation parameter
        beta (float): Decay Parameter
        n (float): Amount of Orders
        delta_t (float): Time split into x equispaced distance
        n_integral (int): N discrete steps for integral

    Returns:
        float: Execution Price for N Orders
    """
    price_one_order = exec_price_one_order(symbol, total_q, theta, order_type, ct, n_integral)

    component_one = (
        delta
        * ((lambda2 - lambda1) / (n * (alpha_self + alpha_cross + beta)))
        * (
            n
            - (
                (1 - np.exp((-1*(alpha_self + alpha_cross) - beta) * n * delta_t))
                / (1 - np.exp((-1*(alpha_self + alpha_cross) - beta) * delta_t))
            )
        )
    )

    component_two_power_base = 1 - np.exp((-1*(alpha_self + alpha_cross) - beta) * delta_t)
    component_two = ((alpha_self+alpha_cross) * ct * total_q / (np.power(n, 2) * (alpha_self + alpha_cross + beta))) * (
        (n * (n - 1) / 2)
        - (
            (n * np.exp(-1*(alpha_self + alpha_cross) - beta * delta_t))
            / (1 - np.exp((-1*(alpha_self + alpha_cross) - beta) * delta_t))
        )
        + (
            (
                (1 - np.exp((-1*(alpha_self + alpha_cross) - beta) * n * delta_t))
                / (np.power(component_two_power_base, 2))
            )
            * np.exp((-1*(alpha_self + alpha_cross) - beta) * delta_t)
        )
    )
    return price_one_order + component_one - component_two
