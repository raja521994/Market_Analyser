from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.prebuilt import create_react_agent
import yfinance as yf
from duckduckgo_search import DDGS
from datetime import datetime
import os
from dotenv import load_dotenv
from system_prompt import SYSTEM_PROMPT

load_dotenv()

# Initialize Groq model
llm = ChatGroq(
    model="openai/gpt-oss-20b",   # Fast + strong model
    temperature=0.2,
    api_key=os.getenv("GROQ_API_KEY")
)

# ==================== TOOLS ====================

@tool
def get_stock_info(ticker: str) -> str:
    """
    Get current price, key statistics and basic info for an Indian stock.
    Use NSE ticker with .NS (e.g. RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS)
    """
    try:
        if not ticker.endswith((".NS", ".BO")):
            ticker = ticker + ".NS"
        
        stock = yf.Ticker(ticker)
        info = stock.info
        
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
        
        result = f"""
Stock: {info.get('longName', ticker)}
Ticker: {ticker}
Current Price: ₹{current_price}
Previous Close: ₹{info.get('previousClose')}
Open: ₹{info.get('open')}
Day High: ₹{info.get('dayHigh')}
Day Low: ₹{info.get('dayLow')}
52 Week High: ₹{info.get('fiftyTwoWeekHigh')}
52 Week Low: ₹{info.get('fiftyTwoWeekLow')}
Market Cap: {info.get('marketCap')}
PE Ratio (Trailing): {info.get('trailingPE')}
Forward PE: {info.get('forwardPE')}
PB Ratio: {info.get('priceToBook')}
Dividend Yield: {info.get('dividendYield')}
EPS: {info.get('trailingEps')}
Book Value: {info.get('bookValue')}
ROE: {info.get('returnOnEquity')}
Debt to Equity: {info.get('debtToEquity')}
Current Ratio: {info.get('currentRatio')}
Sector: {info.get('sector')}
Industry: {info.get('industry')}
Data Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        return result
    except Exception as e:
        return f"Error fetching stock info for {ticker}: {str(e)}"


@tool
def get_historical_data(ticker: str, period: str = "1y") -> str:
    """
    Get historical price data and calculate basic performance metrics.
    period examples: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    """
    try:
        if not ticker.endswith((".NS", ".BO")):
            ticker = ticker + ".NS"
            
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        
        if hist.empty:
            return f"No historical data found for {ticker}"
        
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        change_pct = ((end_price - start_price) / start_price) * 100
        
        high = hist['High'].max()
        low = hist['Low'].min()
        
        hist['SMA20'] = hist['Close'].rolling(20).mean()
        hist['SMA50'] = hist['Close'].rolling(50).mean()
        hist['SMA200'] = hist['Close'].rolling(200).mean()
        
        latest = hist.iloc[-1]
        
        result = f"""
Historical Data for {ticker} (Period: {period})
Start Price: ₹{start_price:.2f}
Current Price: ₹{end_price:.2f}
Change: {change_pct:.2f}%
Period High: ₹{high:.2f}
Period Low: ₹{low:.2f}
Current SMA20: ₹{latest.get('SMA20', float('nan')):.2f}
Current SMA50: ₹{latest.get('SMA50', float('nan')):.2f}
Current SMA200: ₹{latest.get('SMA200', float('nan')):.2f}
Data points: {len(hist)}
Last updated: {hist.index[-1].strftime('%Y-%m-%d')}
"""
        return result
    except Exception as e:
        return f"Error fetching historical data: {str(e)}"


@tool
def search_web(query: str) -> str:
    """
    Search the web for latest news, company announcements, or any information.
    Useful for recent news, earnings, management commentary, policy changes etc.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=6))
        
        if not results:
            return "No results found."
        
        output = f"Search results for: {query}\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r.get('title')}\n"
            output += f"   {r.get('body')}\n"
            output += f"   Source: {r.get('href')}\n\n"
        
        return output
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def get_financials(ticker: str) -> str:
    """
    Get key financial statements summary for an Indian stock.
    """
    try:
        if not ticker.endswith((".NS", ".BO")):
            ticker = ticker + ".NS"
            
        stock = yf.Ticker(ticker)
        financials = stock.financials
        balance_sheet = stock.balance_sheet
        
        result = f"Financial Summary for {ticker}\n\n"
        
        if financials is not None and not financials.empty:
            result += "Income Statement (latest columns):\n"
            result += str(financials.iloc[:, :3]) + "\n\n"
        
        if balance_sheet is not None and not balance_sheet.empty:
            result += "Balance Sheet (latest columns):\n"
            result += str(balance_sheet.iloc[:, :3]) + "\n"
            
        return result
    except Exception as e:
        return f"Error fetching financials: {str(e)}"


tools = [get_stock_info, get_historical_data, search_web, get_financials]

# ==================== AGENT ====================

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT
)

def run_agent(user_input: str, chat_history: list = None):
    if chat_history is None:
        chat_history = []
    
    messages = [{"role": "user", "content": user_input}]
    
    result = agent.invoke({"messages": messages})
    
    final_message = result["messages"][-1]
    return final_message.content