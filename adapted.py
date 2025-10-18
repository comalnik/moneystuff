"""
Monte Carlo portfolio simulator + fan chart.

Usage:
    - Edit the params dict at the bottom to change inputs.
    - Run: python monte_carlo_portfolio.py
    - The fan chart is saved to /mnt/data/portfolio_fan_chart.png (and shown).
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter
import random

def simulate_portfolio(initial_investment,
                       monthly_investment,
                       annual_return,
                       annual_volatility,
                       years,
                       n_simulations=2000,
                       steps_per_year=12,
                       seed=None):
    """
    Simulate a stock portfolio using geometric Brownian motion with regular monthly contributions.

    Parameters
    ----------
    initial_investment : float
        Lump-sum invested at time 0.
    monthly_investment : float
        Contribution added at the END of each period (month).
    annual_return : float
        Expected annual return. Accepts 0.07 or 7 (interprets >1 as percent).
    annual_volatility : float
        Annual volatility (std dev). Accepts 0.15 or 15 (interprets >1 as percent).
    years : int or float
        Simulation horizon in years.
    n_simulations : int
        Number of Monte Carlo paths.
    steps_per_year : int
        Time steps per year (12 = monthly).
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    dict with:
      - time_years : array of time points (years)
      - trajectories : ndarray shape (n_simulations, steps+1)
      - percentiles : dict of arrays for p5, p25, p50, p75, p95
      - mean : mean trajectory across simulations
      - final_stats : dict of final percentiles & mean
    """
    # allow percent inputs like 7 for 7%
    mu = annual_return / 100.0 if abs(annual_return) > 1 else annual_return
    sigma = annual_volatility / 100.0 if abs(annual_volatility) > 1 else annual_volatility

    if seed is not None:
        np.random.seed(seed)

    dt = 1.0 / steps_per_year
    steps = int(round(years * steps_per_year))

    # GBM parameters per step
    drift = (mu - 0.5 * sigma**2) * dt
    diffusion = sigma * np.sqrt(dt)

    # draw random normals: shape (n_simulations, steps)
    Z = np.random.normal(size=(n_simulations, steps))
    factors = np.exp(drift + diffusion * Z)  # multiplicative return factor each step

    # prepare storage (include t=0)
    trajectories = np.zeros((n_simulations, steps + 1), dtype=float)
    trajectories[:, 0] = initial_investment

    # simulate: contributions added at the END of each step
    for t in range(steps):
        trajectories[:, t + 1] = trajectories[:, t] * factors[:, t] + monthly_investment

    time_years = np.linspace(0, years, steps + 1)

    # percentiles and mean across simulations
    p5 = np.percentile(trajectories, 5, axis=0)
    p25 = np.percentile(trajectories, 25, axis=0)
    p50 = np.percentile(trajectories, 50, axis=0)
    p75 = np.percentile(trajectories, 75, axis=0)
    p95 = np.percentile(trajectories, 95, axis=0)
    mean = trajectories.mean(axis=0)

    final_stats = {
        'p5': float(p5[-1]),
        'p25': float(p25[-1]),
        'median': float(p50[-1]),
        'p75': float(p75[-1]),
        'p95': float(p95[-1]),
        'mean': float(mean[-1])
    }

    return {
        'time_years': time_years,
        'trajectories': trajectories,
        'percentiles': {'p5': p5, 'p25': p25, 'p50': p50, 'p75': p75, 'p95': p95},
        'mean': mean,
        'final_stats': final_stats
    }


def plot_fan_chart(result, title=None, savepath=None, show=True):
    """
    Plot a fan chart from the simulation result.

    - Shaded 5-95% band
    - Shaded 25-75% band
    - Median (50th percentile) and Mean lines
    """
    x = result['time_years']
    p5 = result['percentiles']['p5']
    p25 = result['percentiles']['p25']
    p50 = result['percentiles']['p50']
    p75 = result['percentiles']['p75']
    p95 = result['percentiles']['p95']
    mean = result['mean']

    plt.figure(figsize=(11,6))

    # 5-95 band
    plt.fill_between(x, p5, p95, alpha=0.18, label='5-95 percentile band')
    # 25-75 band
    plt.fill_between(x, p25, p75, alpha=0.32, label='25-75 percentile band')

    # median and mean
    plt.plot(x, p50, label='Median (50th)', linewidth=1.8)
    plt.plot(x, mean, linestyle='--', label='Mean', linewidth=1.6)

    plt.xlabel('Years')
    plt.ylabel('Portfolio value')
    if title:
        plt.title(title)
    plt.grid(alpha=0.3)
    plt.legend()

    # currency formatting on y-axis
    ax = plt.gca()
    ax.yaxis.set_major_formatter(StrMethodFormatter('${x:,.0f}'))

    plt.tight_layout()

    
    #if savepath:
    #    plt.savefig(savepath, dpi=150)
    #if show:
    #    plt.show()
    #plt.close()


def runsim(n_simulations=10000, years=30, annual_volatility=15, annual_return=7, monthly_investment=0, initial_investment=10000):
    # === Example usage ===
    params = {
        "initial_investment": initial_investment,
        "monthly_investment": monthly_investment,
        "annual_return":  annual_return,      # 7% expected annual return
        "annual_volatility": annual_volatility, # 15% annual volatility
        "years": years,
        "n_simulations": n_simulations,
        "steps_per_year": 12,
        "seed": random.randint(0,1000000)
    }
    seed = random.randint(0,1000000)
    steps_per_year = 12

    result = simulate_portfolio(
        initial_investment=params["initial_investment"],
        monthly_investment=params["monthly_investment"],
        annual_return=params["annual_return"],
        annual_volatility=params["annual_volatility"],
        years=params["years"],
        n_simulations=params["n_simulations"],
        steps_per_year=params["steps_per_year"],
        seed=params["seed"]
    )

    title = (
        f"Monte Carlo Portfolio ({params['years']} yrs) — "
        f"Init ${params['initial_investment']:,.0f}, ${params['monthly_investment']:,.0f}/mo, "
        f"μ={params['annual_return']}%, σ={params['annual_volatility']}%"
    )
    #save_path = "portfolio_fan_chart.png"
    #plot_fan_chart(result, title=title, savepath=save_path, show=True)

     

    final = result['final_stats']
    #print("Final portfolio outcomes after {:,} simulations (after {:d} years):".format(params['n_simulations'], params['years']))
    #print(f"  5th percentile : ${final['p5']:,.2f}")
    #print(f" 25th percentile : ${final['p25']:,.2f}")
    #print(f"  Median (50th)  : ${final['median']:,.2f}")
    #print(f" 75th percentile : ${final['p75']:,.2f}")
    #print(f" 95th percentile : ${final['p95']:,.2f}")
    #print(f"  Mean           : ${final['mean']:,.2f}")
    #print(f"\nSaved fan chart to: {save_path}")

    return result, title


