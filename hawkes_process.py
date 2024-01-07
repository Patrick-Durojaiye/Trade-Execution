import numpy as np
from tick.hawkes import HawkesExpKern


def estimate_hawkes_parameters(timestamps_buy_trades, timestamps_sell_trades, decays=1.0):
    """
    Estimates Hawkes Parameters

    Args:
        timestamps_buy_trades (ndarray): Timestamps of Buy Trades in a Numpy Array
        timestamps_sell_trades (ndarray): Timestamps of Sell Trades in a Numpy Array
        decays (float): Decay Parameter

    Returns:
        float : Hawkes Model Parameters
    """

    model = HawkesExpKern(decays=decays, penalty="elasticnet")

    model.fit([timestamps_buy_trades, timestamps_sell_trades])

    alpha_11 = model.adjacency[0][0]  # alpha (self-excitation of buys)
    alpha_22 = model.adjacency[1][1]  # alpha (self-excitation of sells)
    alpha_12 = model.adjacency[0][1]  # alpha (cross-excitation) how sells influence buys
    alpha_21 = model.adjacency[1][0]  # alpha (cross-excitation) how buys influence sells
    beta = model.decays

    # Total Times Length of Trades Recorded
    total_time = 1 * 60 * 60

    mu1 = estimate_baseline_intensity(
        timestamps=timestamps_buy_trades, total_time=total_time, num_bins=60
    )
    mu2 = estimate_baseline_intensity(
        timestamps=timestamps_sell_trades, total_time=total_time, num_bins=60
    )

    return mu1, mu2, alpha_11, alpha_22, alpha_12, alpha_21, beta


def calculate_intensity(
    t, order_event_times, mu, alpha_self_excitation, alpha_cross_excitation, beta
):
    """
    Calculates the intensity for buys and sells
    Args:
        t (int): Current Timestamp
        order_event_times (ndarray): Timestamps of Buy and Sell Trades in a Numpy Array
        mu: Baseline Intensity
        alpha_self_excitation: Self-Excitation Parameter
        alpha_cross_excitation: Cross-Excitation Parameter
        beta: Decay Parameter

    Returns:
        float: Intensity
    """

    # Computes Time difference
    historic_event_times = t - order_event_times
    decayed_values_self_excitation = alpha_self_excitation * np.exp(
        -beta * historic_event_times
    )
    decayed_values_cross_excitation = alpha_cross_excitation * np.exp(
        -beta * historic_event_times
    )

    intensity_self_excitation = np.sum(decayed_values_self_excitation)
    intensity_cross_excitation = np.sum(decayed_values_cross_excitation)

    return mu + intensity_self_excitation + intensity_cross_excitation


def estimate_baseline_intensity(timestamps, total_time, num_bins):
    """
    Estimation for Baseline Intensity
    Args:
        timestamps (ndarray): Timestamps of Buy and Sell Trades in a Numpy Array
        total_time (int): Time length of recorded BUY/SELL Trades
        num_bins: Number of Intervals

    Returns:
        float: Baseline Intensity
    """
    # Bin the timestamps for buy/sell trades
    counts, _ = np.histogram(timestamps, bins=num_bins)

    baseline_intensity = np.mean(counts) / (total_time / num_bins)
    return baseline_intensity
