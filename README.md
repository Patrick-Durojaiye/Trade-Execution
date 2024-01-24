# Trade Execution with Multivariate Hawkes Stochastic Model

## Description
This project implements a Multivariate Hawkes Stochastic Model to execute large order transactions via TWAP algorithm. The key components of this project include:

- `run.py`: The main script that estimates and sets the parameters for algorithm and also executes the TWAP algorithm.
- `binance_utils.py`: Utilities for interacting with the Binance Exchange API.
- `hawkes_process.py`: Implementation of the Hawkes process and estimates parameters used for the Hawkes model.
- `order_execute.py`: Gathers market liquidity data and price forecastion for executing orders based on calculated parameters.

## Installation
To set up this project, follow these steps:
1. Clone the repository.
2. Install the required dependencies (using the command `pip install -r requirements.txt`).

## Setup
Create a `.env` file based on the `.env.example` file provided, insert your Binance API key inside the .env file.

## Usage
Run `run.py` to start the execution process. Input parameters `symbol, n, order_type, total_q, delta_t, n_integral` to your discretion.

## License
This project is licensed under the MIT License - see the `LICENSE` file for details.
