import time
from order_execute import avg_exec_price, exec_price_one_order
from binance_utils import aggre, measure_liquidity, get_order_book_data, get_tick_size, order
from hawkes_process import estimate_hawkes_parameters, calculate_intensity


def parameters(symbol: str):
    """

    Args:
        symbol (str): Market Symbol e.g. BTCUSDT

    Returns:
        float: Returns paramter values to input into QUASI-TWAP
    """

    current_time = int(round(time.time() * 1000))
    buy_timestamps, sell_timestamps = aggre(symbol=symbol, current_time=current_time)

    buy_timestamps /= 1000
    sell_timestamps /= 1000

    mu1, mu2, alpha_11, alpha_22, alpha_12, alpha_21, beta = estimate_hawkes_parameters(
        timestamps_buy_trades=buy_timestamps, timestamps_sell_trades=sell_timestamps, decays=1.0
    )

    bids, asks = get_order_book_data(symbol=symbol, limit=1000)

    ct = measure_liquidity(bids=bids, asks=asks, mid_price_depth_range=0.005)
    theta = asks["price"].iloc[0] - bids["price"].iloc[0]
    delta = get_tick_size(symbol=symbol)

    current_time /= 1000

    lambda_1 = calculate_intensity(t=current_time, order_event_times=buy_timestamps, mu=mu1,
                                   alpha_self_excitation=alpha_11, alpha_cross_excitation=alpha_12, beta=beta)
    lambda_2 = calculate_intensity(t=current_time, order_event_times=sell_timestamps, mu=mu2,
                                   alpha_self_excitation=alpha_22, alpha_cross_excitation=alpha_21, beta=beta)
    return alpha_11, alpha_22, alpha_12, alpha_21, beta, ct, theta, lambda_1, lambda_2, delta


def quasi_twap(symbol, n, order_type, total_q, lambda1, lambda2, delta_t, n_integral):
    """
    Quasi Twap Algorithm to execute large Buy/Sell orders

    Args:
        symbol (str): Market Symbol e.g. BTCUSDT
        n (int): Amount of Orders
        order_type (int): Denotes if buy or sell order, +1 for buy and -1 for sell
        total_q (float): Total Amount to Trade
        lambda1 (float): Intensity
        lambda2 (float): Intensity
        delta_t (float): Time split into x equispaced distance
        n_integral (int): N discrete steps for integral

    Returns:
        True
    """
    # Quasi-TWAP buy
    if order_type == 1:
        for i in range(0, n):
            alpha_11, alpha_22, alpha_12, alpha_21, beta, ct, theta, lambda_1, lambda_2, delta = \
                parameters(symbol=symbol)

            if avg_exec_price(
                    symbol,
                    total_q,
                    theta,
                    order_type,
                    ct,
                    delta,
                    lambda1,
                    lambda2,
                    alpha_11,
                    alpha_12,
                    beta,
                    n,
                    delta_t,
                    n_integral
            ) < exec_price_one_order(symbol, total_q * (n - i) / n, theta, order_type, ct, n_integral):
                order(symbol=symbol, order_type=order_type, size=total_q / n)
                # reduce quantity
                time.sleep(delta_t)
            else:

                order(symbol=symbol, order_type=order_type, size=total_q * (n - i) / n)
                break

    # Quasi-TWAP sell
    elif order_type == -1:
        for i in range(0, n):
            alpha_11, alpha_22, alpha_12, alpha_21, beta, ct, theta, lambda_1, lambda_2, delta = \
                parameters(symbol=symbol)

            if avg_exec_price(
                    symbol,
                    total_q,
                    theta,
                    order_type,
                    ct,
                    delta,
                    lambda1,
                    lambda2,
                    alpha_22,
                    alpha_21,
                    beta,
                    n,
                    delta_t,
                    n_integral
            ) > exec_price_one_order(symbol, total_q * (n - i) / n, theta, order_type, ct, n_integral):
                order(symbol=symbol, order_type=order_type, size=total_q / n)
                time.sleep(delta_t)
            else:
                order(symbol=symbol, order_type=order_type, size=total_q * (n - i) / n)
                break
    return True

# Call the quasi_twap to run the model
