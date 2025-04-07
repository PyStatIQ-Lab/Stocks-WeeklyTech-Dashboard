import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# Set page config
st.set_page_config(
    page_title="Stock Technical Indicators Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .positive {
        color: #28a745;
    }
    .negative {
        color: #dc3545;
    }
    .stock-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .indicator-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# Define the base URL
base_url = "https://priceapi.moneycontrol.com/pricefeed/techindicator/W/"

# Define headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive'
}

# Load stock symbols from the Excel file
@st.cache_data
def load_stock_symbols():
    try:
        symbols_df = pd.read_excel('stock_symbols.xlsx')
        return symbols_df['Symbol'].str.replace('.NS', '').tolist()
    except Exception as e:
        st.error(f"Failed to load stock symbols: {str(e)}")
        return []

# Function to get ISIN from NSE
def get_isin(symbol):
    try:
        # Create a session and get cookies first
        s = requests.Session()
        s.get("https://www.nseindia.com/", headers=headers, timeout=10)
        
        # Then make the API request
        nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
        r = s.get(nse_url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            return r.json()['metadata']['isin']
        else:
            st.warning(f"NSE API returned status code {r.status_code} for {symbol}")
            return None
    except Exception as e:
        st.warning(f"Failed to fetch ISIN for {symbol}: {str(e)}")
        return None

# Function to get sc_id from ISIN or symbol directly
def get_sc_id(identifier, is_isin=True):
    try:
        query_type = 1 if is_isin else 2  # 1 for ISIN, 2 for symbol
        money_control_suggestion_url = f'https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php?classic=true&query={identifier}&type={query_type}&format=json'
        money_control_res = requests.get(money_control_suggestion_url, headers=headers, timeout=10)
        
        if money_control_res.status_code == 200 and money_control_res.json():
            result = money_control_res.json()[0]
            return result['sc_id'], result['stock_name']
        return None, None
    except Exception as e:
        st.warning(f"Failed to fetch MoneyControl ID for {identifier}: {str(e)}")
        return None, None

# Function to fetch technical indicators
def fetch_technical_indicators(sc_id):
    try:
        url = f"{base_url}{sc_id}"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"MoneyControl API returned status code {response.status_code}")
            return None
    except Exception as e:
        st.warning(f"Failed to fetch technical indicators: {str(e)}")
        return None

# Function to display technical indicators
def display_technical_indicators(data, stock_name):
    if not data:
        st.warning("No data available for this stock.")
        return
    
    # Create a card for the stock
    with st.container():
        st.markdown(f"<div class='stock-card'><h2>{stock_name}</h2>", unsafe_allow_html=True)
        
        # Try to display price information if available
        price_data = data.get('data', {}).get('priceinfo', {})
        if price_data:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Current Price", f"₹{price_data.get('lastprice', 'N/A')}")
            with col2:
                change = price_data.get('change', 0)
                change_pct = price_data.get('percentchange', 0)
                st.metric("Change", f"₹{change}", f"{change_pct}%", delta_color="normal")
            with col3:
                st.metric("High", f"₹{price_data.get('high', 'N/A')}")
            with col4:
                st.metric("Low", f"₹{price_data.get('low', 'N/A')}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Check for technical indicators
    indicators = data.get('data', {}).get('techindicator', [])
    
    if not indicators:
        st.warning("No technical indicators found in the response.")
        with st.expander("View Raw API Response"):
            st.json(data)
        return
    
    # Display indicators in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("Trend Indicators")
        for indicator in indicators:
            if 'MA' in indicator.get('name', '') or 'Moving Average' in indicator.get('name', ''):
                with st.container():
                    st.markdown(f"""
                    <div class="indicator-card">
                        <h4>{indicator.get('name', 'Indicator')}</h4>
                        <p><strong>Value:</strong> {indicator.get('value', 'N/A')}</p>
                        <p><strong>Signal:</strong> {indicator.get('signal', 'N/A')}</p>
                        <p><strong>Action:</strong> <span class="{'positive' if indicator.get('action', '').lower() == 'buy' else 'negative'}">{indicator.get('action', 'N/A')}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("Momentum Indicators")
        for indicator in indicators:
            if 'RSI' in indicator.get('name', '') or 'MACD' in indicator.get('name', ''):
                with st.container():
                    st.markdown(f"""
                    <div class="indicator-card">
                        <h4>{indicator.get('name', 'Indicator')}</h4>
                        <p><strong>Value:</strong> {indicator.get('value', 'N/A')}</p>
                        <p><strong>Signal:</strong> {indicator.get('signal', 'N/A')}</p>
                        <p><strong>Action:</strong> <span class="{'positive' if indicator.get('action', '').lower() == 'buy' else 'negative'}">{indicator.get('action', 'N/A')}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
    
    with col3:
        st.subheader("Other Indicators")
        for indicator in indicators:
            if 'MA' not in indicator.get('name', '') and 'RSI' not in indicator.get('name', '') and 'MACD' not in indicator.get('name', ''):
                with st.container():
                    st.markdown(f"""
                    <div class="indicator-card">
                        <h4>{indicator.get('name', 'Indicator')}</h4>
                        <p><strong>Value:</strong> {indicator.get('value', 'N/A')}</p>
                        <p><strong>Signal:</strong> {indicator.get('signal', 'N/A')}</p>
                        <p><strong>Action:</strong> <span class="{'positive' if indicator.get('action', '').lower() == 'buy' else 'negative'}">{indicator.get('action', 'N/A')}</span></p>
                    </div>
                    """, unsafe_allow_html=True)

# Main app
def main():
    st.title("📈 Stock Technical Indicators Dashboard")
    st.markdown("Get technical analysis indicators for Indian stocks from MoneyControl")
    
    # Load stock symbols
    stock_symbols = load_stock_symbols()
    
    if not stock_symbols:
        st.error("No stock symbols loaded. Please check the Excel file.")
        st.stop()
    
    # Search options
    selected_symbol = st.selectbox("Select a stock symbol:", stock_symbols)
    
    if st.button("Get Technical Indicators"):
        with st.spinner(f"Fetching data for {selected_symbol}..."):
            try:
                # First try to get ISIN from NSE
                isin = get_isin(selected_symbol)
                
                # Then get sc_id from MoneyControl - first try with ISIN, then fallback to symbol
                sc_id, stock_name = None, None
                if isin:
                    sc_id, stock_name = get_sc_id(isin, is_isin=True)
                
                if not sc_id:
                    # Fallback to search by symbol if ISIN search failed
                    sc_id, stock_name = get_sc_id(selected_symbol, is_isin=False)
                
                if sc_id:
                    # Finally get technical indicators
                    data = fetch_technical_indicators(sc_id)
                    
                    if data:
                        display_technical_indicators(data, stock_name or selected_symbol)
                    else:
                        st.error("Failed to fetch technical indicators.")
                else:
                    st.error("Could not find stock on MoneyControl.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    
    # Add footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 14px;">
        <p>Data provided by MoneyControl API | Updated at {}</p>
        <p>Note: This app is for educational purposes only. Not investment advice.</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
