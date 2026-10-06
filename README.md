# StockCorrelation

A small Python tool for analysing how diversified a portfolio of stocks or ETFs
really is. It loads daily price histories, measures how strongly the holdings move
together, flags redundant positions, proposes a reduced portfolio and suggested
weights, and charts the growth of both.

## How it works

1. **Load** — every CSV in a directory becomes a `Stock`. The ticker is taken from
   the first word of the file name (the format of investing.com "Historical Data"
   downloads, e.g. `VUSA ETF Stock Price History.csv`). Numbers are cleaned of
   thousands separators and `Change %` is parsed into a float.
2. **Correlate** — daily `Change %` series are aligned on common dates and a
   correlation matrix is computed. Each stock's volatility is the standard
   deviation of its daily changes.
3. **Bucket** — correlations are bucketed into `-2..2`
   (`≥ 0.8 → 2`, `≥ 0.5 → 1`, `≤ -0.5 → -1`, `≤ -0.8 → -2`, otherwise `0`).
   Pairs in bucket `2` are "strongly correlated".
4. **Score** — each stock gets a penalty
   `redundancy + average correlation + volatility`, where redundancy is the number
   of strongly correlated partners, and a diversification score `1 / (1 + penalty)`.
5. **Weight** — suggested weights are proportional to
   `diversification / volatility`, floored at 1% and renormalised.
6. **Reduce** — a reduced portfolio is built by walking the stocks and skipping any
   that are strongly correlated with one already chosen.
7. **Report** — prints a summary per stock, the correlated pairs (with the more
   volatile of each pair), and the suggested weights; draws a correlation cluster
   map and a "growth of $1" chart for equal and suggested weights.

## Requirements

- Python 3.10+
- `pandas`, `numpy`, `matplotlib`, `seaborn`

```sh
pip install pandas numpy matplotlib seaborn
```

## Usage

```sh
python main.py
```

`main.py` analyses the ETFs in `example_data/`, builds a reduced portfolio, prints
both summaries, and opens the charts. To analyse your own holdings, drop
investing.com CSV exports into a directory and point
`Portfolio.generateFromDirectory` at it.

## Files

| File | Description |
|------|-------------|
| `main.py` | Example run over `example_data/` |
| `Portfolio.py` | Correlation, scoring, weighting, reduction and plotting |
| `Stock.py` | CSV loading and cleaning for one ticker |
| `example_data/` | Sample daily price histories for UK-listed ETFs |

## Limitations

- Ticker extraction splits the path on `\`, so it only produces clean tickers on
  Windows; on Linux/macOS the directory prefix ends up in the ticker name.
- Only the `Change %` column is used; prices and volumes are ignored.
