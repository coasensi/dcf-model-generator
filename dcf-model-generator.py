import requests
import yfinance as yf
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# function to fetch data from alpha vantage
def fetch_data(function, symbol, api_key):
    url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    return data

# function to extract financial data
def extract_financial_data(income_statement, balance_sheet, cash_flow):
    revenue = float(income_statement['annualReports'][0]['totalRevenue'])
    ebit = float(income_statement['annualReports'][0]['ebit'])
    net_income = float(income_statement['annualReports'][0]['netIncome'])
    total_assets = float(balance_sheet['annualReports'][0]['totalAssets'])
    total_liabilities = float(balance_sheet['annualReports'][0]['totalLiabilities'])
    equity = float(balance_sheet['annualReports'][0]['totalShareholderEquity'])
    operating_cash_flow = float(cash_flow['annualReports'][0]['operatingCashflow'])
    capital_expenditures = float(cash_flow['annualReports'][0]['capitalExpenditures'])
    
    return {
        'revenue': revenue,
        'ebit': ebit,
        'net_income': net_income,
        'total_assets': total_assets,
        'total_liabilities': total_liabilities,
        'equity': equity,
        'operating_cash_flow': operating_cash_flow,
        'capital_expenditures': capital_expenditures
    }

symbol = input("Enter the stock symbol: ")
api_key = input("Enter your Alpha Vantage API key: ")
beta = float(input("Enter the stock's beta: "))
market_return = float(input("Enter the expected market return (e.g., 0.08 for 8%): "))
cost_of_debt = float(input("Enter the cost of debt (e.g., 0.04 for 4%): "))
tax_rate = float(input("Enter the tax rate (e.g., 0.21 for 21%): "))
growth_rate = float(input("Enter the growth rate (e.g., 0.05 for 5%): "))
terminal_growth_rate = float(input("Enter the terminal growth rate (e.g., 0.02 for 2%): "))
years = int(input("Enter the number of years for projection: "))

# fetch financial data
income_statement = fetch_data('INCOME_STATEMENT', symbol, api_key)
balance_sheet = fetch_data('BALANCE_SHEET', symbol, api_key)
cash_flow = fetch_data('CASH_FLOW', symbol, api_key)

financial_data = extract_financial_data(income_statement, balance_sheet, cash_flow)

# free cash flow calculation
fcf = financial_data['operating_cash_flow'] - financial_data['capital_expenditures']

# fetch the risk-free rate (e.g., from 10-year us treasury bond)
risk_free_rate_data = yf.download('^TNX', period='1d')
risk_free_rate = risk_free_rate_data['Close'][0] / 100

# wacc calculation
cost_of_equity = risk_free_rate + beta * (market_return - risk_free_rate)
equity = financial_data['equity']
debt = financial_data['total_liabilities']
total_value = equity + debt
weight_equity = equity / total_value
weight_debt = debt / total_value
wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))

# future projections
future_fcfs = [fcf * (1 + growth_rate)**i for i in range(1, years + 1)]

# terminal value calculation
terminal_value = future_fcfs[-1] * (1 + terminal_growth_rate) / (wacc - terminal_growth_rate)

# discounting future cash flows to present value
discounted_fcfs = [fcf / (1 + wacc)**i for i, fcf in enumerate(future_fcfs, start=1)]
discounted_terminal_value = terminal_value / (1 + wacc)**years

# dcf valuation
dcf_value = sum(discounted_fcfs) + discounted_terminal_value

# create dataframe for projections
projections = pd.DataFrame({
    'year': list(range(1, years + 1)),
    'future fcf': future_fcfs,
    'discounted fcf': discounted_fcfs
})

# output the results
print(f"free cash flow: ${fcf:,.2f}")
print(f"risk-free rate: {risk_free_rate:.2%}")
print(f"cost of equity: {cost_of_equity:.2%}")
print(f"wacc: {wacc:.2%}")
print(f"future fcfs: {[f'${fcf:,.2f}' for fcf in future_fcfs]}")
print(f"terminal value: ${terminal_value:,.2f}")
print(f"discounted fcfs: {[f'${fcf:,.2f}' for fcf in discounted_fcfs]}")
print(f"discounted terminal value: ${discounted_terminal_value:,.2f}")
print(f"dcf valuation: ${dcf_value:,.2f}")

# plot future fcfs and discounted fcfs
plt.figure(figsize=(12, 6))
plt.plot(projections['year'], projections['future fcf'], marker='o', label='future fcf')
plt.plot(projections['year'], projections['discounted fcf'], marker='x', label='discounted fcf')
plt.xlabel('year')
plt.ylabel('usd')
plt.title(f'projected and discounted free cash flows for {symbol}')
plt.legend()
plt.grid(True)
plt.show()

# create table for projections
print("\nprojections table:")
print(projections)

# create summary table for key metrics
summary = pd.DataFrame({
    'metric': ['free cash flow', 'risk-free rate', 'cost of equity', 'wacc', 'terminal value', 'dcf valuation'],
    'value': [f"${fcf:,.2f}", f"{risk_free_rate:.2%}", f"{cost_of_equity:.2%}", f"{wacc:.2%}", f"${terminal_value:,.2f}", f"${dcf_value:,.2f}"]
})

print("\nsummary table:")
print(summary)
