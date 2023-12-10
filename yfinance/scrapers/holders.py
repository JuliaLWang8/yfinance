from io import StringIO

import pandas as pd

from yfinance.data import YfData


class Holders:
    _SCRAPE_URL_ = 'https://finance.yahoo.com/quote'

    def __init__(self, data: YfData, symbol: str, proxy=None):
        self._data = data
        self._symbol = symbol
        self.proxy = proxy

        self._major = None
        self._institutional = None
        self._mutualfund = None

        self._insider_transactions = None
        self._insider_purchases = None
        self._insider_roster = None

    @property
    def major(self) -> pd.DataFrame:
        if self._major is None:
            self._scrape(self.proxy)
        return self._major

    @property
    def institutional(self) -> pd.DataFrame:
        if self._institutional is None:
            self._scrape(self.proxy)
        return self._institutional

    @property
    def mutualfund(self) -> pd.DataFrame:
        if self._mutualfund is None:
            self._scrape(self.proxy)
        return self._mutualfund
    
    @property
    def insider_transactions(self) -> pd.DataFrame:
        if self._insider_transactions is None:
            self._scrape_insider_transactions(self.proxy)
        return self._insider_transactions
    
    @property
    def insider_purchases(self) -> pd.DataFrame:
        if self._insider_purchases is None:
            self._scrape_insider_transactions(self.proxy)
        return self._insider_purchases
    
    @property
    def insider_roster(self) -> pd.DataFrame:
        if self._insider_roster is None:
            self._scrape_insider_ros(self.proxy)
        return self._insider_roster

    def _scrape(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/holders', proxy=proxy)
            holders = pd.read_html(StringIO(resp.text))
        except Exception:
            holders = []

        if len(holders) >= 3:
            self._major = holders[0]
            self._institutional = holders[1]
            self._mutualfund = holders[2]
        elif len(holders) >= 2:
            self._major = holders[0]
            self._institutional = holders[1]
        elif len(holders) >= 1:
            self._major = holders[0]

        if self._institutional is not None:
            if 'Date Reported' in self._institutional:
                self._institutional['Date Reported'] = pd.to_datetime(
                    self._institutional['Date Reported'])
            if '% Out' in self._institutional:
                self._institutional['% Out'] = self._institutional[
                                                   '% Out'].str.replace('%', '').astype(float) / 100

        if self._mutualfund is not None:
            if 'Date Reported' in self._mutualfund:
                self._mutualfund['Date Reported'] = pd.to_datetime(
                    self._mutualfund['Date Reported'])
            if '% Out' in self._mutualfund:
                self._mutualfund['% Out'] = self._mutualfund[
                                                '% Out'].str.replace('%', '').astype(float) / 100
    
    def _scrape_insider_transactions(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/insider-transactions', proxy=proxy)
            insider_transactions = pd.read_html(StringIO(resp.text))
        except Exception:
            insider_transactions = []

        if len(insider_transactions) >= 3:
            self._insider_purchases = insider_transactions[0]
            self._insider_transactions = insider_transactions[2]
        elif len(insider_transactions) >= 2:
            self._insider_purchases = insider_transactions[0]
        elif len(insider_transactions) >= 1:
            self._insider_transactions = insider_transactions[0]

        if self._insider_transactions is not None:
            holders = self._insider_transactions

            def split_insider_title(input_string):
                import re
                parts = input_string.split(' ')

                for i, part in enumerate(parts):
                    if not re.match(r'^[A-Z]+\.*-*[A-Z]*$', part):
                        name_part = ' '.join(parts[:i])
                        title_part = ' '.join(parts[i:])
                        return [name_part.strip(), title_part.strip()]

                return [input_string]
            holders.loc[:, ['Insider', 'Position']] = holders['Insider']\
                .apply(split_insider_title).apply(lambda x: pd.Series(x, index=['Insider', 'Position']))
            
            holders = holders[['Insider', 'Position'] + holders.columns\
                              .difference(['Insider', 'Position']).tolist()]

            holders.fillna('N/A', inplace=True) 
            self._insider_transactions = holders

        if self._insider_purchases is not None:
            holders = self._insider_purchases
            
            holders.fillna('N/A', inplace=True) 
            self._insider_purchases = holders


    def _scrape_insider_ros(self, proxy):
        ticker_url = f"{self._SCRAPE_URL_}/{self._symbol}"
        try:
            resp = self._data.cache_get(ticker_url + '/insider-roster', proxy=proxy)
            insider_roster = pd.read_html(StringIO(resp.text))
        except Exception:
            insider_roster = []

        if len(insider_roster) >= 1:
            self._insider_roster = insider_roster[0]

        if self._insider_roster is not None:
            holders = self._insider_roster

            holders = holders[:-1]  # Remove the last row

            def split_name_title(input_string):
                import re
                parts = input_string.split(' ')

                for i, part in enumerate(parts):
                    if not re.match(r'^[A-Z]+\.*-*[A-Z]*$', part):
                        name_part = ' '.join(parts[:i])
                        title_part = ' '.join(parts[i:])
                        return [name_part.strip(), title_part.strip()]

                return [input_string]
            holders.loc[:, ['Individual or Entity', 'Position']] = holders['Individual or Entity']\
                .apply(split_name_title).apply(lambda x: pd.Series(x, index=['Individual or Entity', 'Position']))
            
            holders = holders[['Individual or Entity', 'Position'] + holders.columns\
                              .difference(['Individual or Entity', 'Position']).tolist()]

            self._insider_roster = holders

