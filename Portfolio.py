from __future__ import annotations
from Stock import Stock
import pandas as pd
from pathlib import Path
import numpy as np
from pprint import pprint
import seaborn as sns
import matplotlib.pyplot as plt

from typing import TypedDict, Hashable, Any

class StockSummary(TypedDict):
    ticker: str
    volatility: float
    relationships: dict[Hashable, Any]
    redundancy_score: float
    avg_correlation: float
    score: float
    diversification: float
    strong_connections: list[Hashable]


class Portfolio:

    # read stock data. assumes that the ticker is the firrst work in the file name, downloaded frorm investing.com
    @staticmethod
    def generateFromDirectory(dir:str, name:str) -> Portfolio:
        csv_paths = [str(p) for p in Path(dir).glob("*.csv")]
        stocks:list[Stock] = []
        for p in csv_paths:
            ticker = p.split("\\")[-1].split(" ")[0]
            stocks.append(Stock(p, ticker))
        return Portfolio(name, stocks)

    def __init__(self, name:str, stocks:list[Stock]) -> None:
        self.name = name
        self.stocks:list[Stock] = stocks

        self.changes = self.get_changes() # pct change matrix

        self.correlation = self.changes.corr() # correlation matrix

        self.average_correlations = self.correlation.mean(axis=1) # avg. correlation per stock

        self.volatilities = self.changes.std() # standard deviation is volatility

        self.bucketed_correlation = self.bucket_correlation_matrix(self.correlation) # buckets ranges in [-2,2]

        self.correlated_pairs = self.get_correlated_pairs() # pairs of stocks with 2 correlation

        self.redundacies:pd.Series = (self.bucketed_correlation == 2).sum(axis=1) # number of highly correlated stocks per stock

        (self.stock_summaries, self.sorted_stock_summaries) = self.generate_stock_summaries()

        self.suggested_weights = self.generate_suggested_weights(self.sorted_stock_summaries)

        self.summary = self.generate_summary()

    def get_correlated_pairs(self):
        correlated_pairs = (
            self.bucketed_correlation
            .where(np.triu(np.ones(self.bucketed_correlation.shape), k=1).astype(bool))
            .stack()
            .reset_index()
        )

        correlated_pairs.columns = ["Stock A", "Stock B", "Bucket"]

        correlated_pairs = correlated_pairs[correlated_pairs["Bucket"] == 2]

        ordered_pairs: list[dict[str,str]] = []

        for _, row in correlated_pairs.iterrows():
            a, b = row["Stock A"], row["Stock B"]
            vol_a = self.volatilities[a]
            vol_b = self.volatilities[b]

            if vol_a > vol_b:
                ordered_pairs.append({'stock_a':a, 'stock_b':b, 'most_volatile':a})
            else:
                ordered_pairs.append({'stock_a':a, 'stock_b':b, 'most_volatile':b})

        return ordered_pairs

    def generate_stock_summaries(self):
        stock_summaries: list[StockSummary] = []
        for stock in self.stocks:
            score = self.score_stock(stock)
            summary: StockSummary = {
                    "ticker": stock.ticker,
                    "volatility": self.volatilities[stock.ticker],
                    "relationships": self.bucketed_correlation.loc[stock.ticker].to_dict(),
                    "redundancy_score": self.redundacies[stock.ticker],
                    "avg_correlation": self.average_correlations[stock.ticker],
                    "score": score,
                    "diversification": 1 / (1 + score),
                    "strong_connections":[other for other, bucket in self.bucketed_correlation.loc[stock.ticker].to_dict().items() if bucket == 2]
            }

            stock_summaries.append(summary)

        return (stock_summaries, sorted(
            stock_summaries,
            key=lambda s: s["diversification"],
            reverse=True
        ))

    def generate_suggested_weights(self, summaries: list[StockSummary]):
        hybrid = {
            s["ticker"]: float(s["diversification"]) / float(s["volatility"])
            for s in summaries
        }

        total = sum(hybrid.values())
        weighted = {t: w / total for t, w in hybrid.items()}

        floor = 0.01
        floored = {t: max(w, floor) for t, w in weighted.items()}

        total = sum(floored.values())
        final_weights = {t: w / total for t, w in floored.items()}

        return final_weights

    def generate_summary(self):
        return {
            "stock_summaries": self.stock_summaries,
            "correlated_pairs": self.correlated_pairs,
            "suggested_weights": self.suggested_weights
        }

    def get_changes(self) -> pd.DataFrame:
        series = [s.data["Change %"].rename(s.ticker) for s in self.stocks]
        aligned = pd.concat(series, axis=1, join="inner").dropna()
        return aligned

    @staticmethod
    def bucket_correlation_matrix(df:pd.DataFrame):
        def bucket_corr(x:float):
            if x >= 0.8:
                return 2
            elif x >= 0.5:
                return 1
            elif x <= -0.8:
                return -2
            elif x <= -0.5:
                return -1
            else:
                return 0
        df = df.map(bucket_corr)
        np.fill_diagonal(df.values, 0)
        return df


    def score_stock(self, stock:Stock):
        return (
          self.redundacies[stock.ticker]
          + self.average_correlations[stock.ticker]
          + self.volatilities[stock.ticker]
        )

    def print_summary(self):
        print(f"\n=== PORTFOLIO: {self.name} ===")

        print("\n=== Stock Summaries ===")
        for s in self.summary["stock_summaries"]:
            print(f"\n  Ticker:             {s['ticker']}")
            print(f"  Volatility:         {s['volatility']:.2f}")
            print(f"  Diversification:    {s['diversification']:.6f}")
            print(f"  Penalty:            {s['score']:.6f}")
            print(f"  Avg Correlation:    {s['avg_correlation']:.6f}")
            print(f"  Redundancy Score:   {s['redundancy_score']}")
            print(f"  Strong Connections: {s['strong_connections']}")

        print("\n=== Correlated Pairs ===")
        for pair in self.summary["correlated_pairs"]:
            print(f"  {pair['stock_a']} ↔ {pair['stock_b']}  "
                  f"(most volatile: {pair['most_volatile']})")

        print("\n=== Suggested Weights ===")
        for stock, weight in self.suggested_weights.items():
            print(f"  {stock}: {weight:.2%}")

    def generate_clustermap(self, fig_name:str):
        sns.clustermap(
            self.correlation,
            cmap="coolwarm",
            linewidths=0.5,
            annot=False,
            figsize=(8, 8)
        )
        plt.tight_layout(pad=2.5)
        plt.title(fig_name)

    def reduce_portfolio(self, new_name:str) -> Portfolio:
        stock_by_ticker = {s.ticker: s for s in self.stocks}


        portfolio = []
        selected = set()

        for summary in self.stock_summaries:
            strong_links = [
                other for other, bucket in summary["relationships"].items()
                if bucket == 2
            ]

            # Check if this stock conflicts with anything already selected
            conflict = any(link in selected for link in strong_links)

            if not conflict:
                portfolio.append(stock_by_ticker[summary["ticker"]])
                selected.add(summary["ticker"])

        return Portfolio(new_name, portfolio)

    def get_returns(self, weights):
        portfolio_returns = self.changes / 100
        portfolio_returns = portfolio_returns.mul(pd.Series(weights)).sum(axis=1)
        return (1 + portfolio_returns).cumprod()


    def graph_returns(self, equal_weight=False):
        plt.figure(figsize=(10,5))
        if equal_weight:
            w = {s.ticker: 1.0 / len(self.stocks) for s in self.stocks}
        else:
            w = self.suggested_weights

        returns = self.get_returns(w)

        vol = float(returns.std())
        plt.plot(returns, label="Portfolio")
        plt.title(f"Weighted Portfolio Growth ({self.name}, {equal_weight=}, {vol=})")
        plt.ylabel("Growth of $1")
        plt.xlabel("Day")
        plt.grid(True)
        plt.legend()

