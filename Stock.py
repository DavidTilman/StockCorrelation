import pandas as pd
import numpy as np

class Stock:
    def __init__(self, path:str, ticker:str) -> None:
        self.ticker = ticker
        self.path = path
        self.data = pd.read_csv(self.path)
        self._clean()

    def _clean(self):
        # clean numerics
        for col in self.data.columns:
          if self.data[col].dtype == object:
              # remove commas
              self.data[col] = self.data[col].str.replace(",", "", regex=False)

              # convert to numeric where possible
              try:
                self.data[col] = pd.to_numeric(self.data[col])
              except:
                  continue


        self.data["Date"] = pd.to_datetime(self.data["Date"], format="%m/%d/%Y")
        self.data["Change %"] = self.data["Change %"].str.rstrip("%").astype(float)
        self.data["Change %"] = pd.to_numeric(self.data["Change %"])
        self.data.set_index("Date").sort_index()






