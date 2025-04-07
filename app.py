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
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: white;
    }
    .stTextInput input {
        background-color: white;
    }
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-title {
        font-size: 14px;
        color: #666;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
    }
    .positive {
        color: #28a745;
    }
    .negative {
        color: #dc3545;
    }
    .header {
        color: #2c3e50;
    }
    .stock-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Define the base URL
base_url = "https://priceapi.moneycontrol.com/pricefeed/techindicator/W/"

# Define headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'
}

# Load stock symbols from the Excel file
@st.cache_data
def load_stock_symbols():
    try:
        symbols_df = pd.read_excel('stock_symbols.xlsx')
        return symbols_df['Symbol'].str.replace('.NS', '').tolist()
    except:
        st.error("Failed to load stock symbols. Please ensure 'stock_symbols.xlsx' is in the correct location.")
        return []

# Function to get sc_id from ISIN
def get_sc_id(isin):
    try:
        money_control_suggestion_url = f'https://www.moneycontrol.com/mccode/common/autosuggestion_solr.php?classic=true&query={isin}&type=1&format=json'
        money_control_res = requests.get(money_control_suggestion_url, headers=headers)
        if money_control_res.status_code == 200 and money_control_res.json():
            return money_control_res.json()[0]['sc_id'], money_control_res.json()[0]['stock_name']
        return None, None
    except:
        return None, None

# Function to fetch technical indicators
def fetch_technical_indicators(sc_id):
    url = f"{base_url}{sc_id}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    return None

# Function to display technical indicators in a nice format
def display_technical_indicators(data, stock_name):
    if not data:
        st.warning("No technical indicator data available for this stock.")
        return
    
    indicators = data.get('data', {}).get('techindicator', [])
    price_data = data.get('data', {}).get('priceinfo', {})
    
    if not indicators:
        st.warning("No technical indicators found in the response.")
        return
    
    # Create a card for the stock
    with st.container():
        st.markdown(f"<div class='stock-card'><h2 class='header'>{stock_name}</h2>", unsafe_allow_html=True)
        
        # Display price information
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Price", f"₹{price_data.get('lastprice', 'N/A')}")
        with col2:
            change = price_data.get('change', 0)
            change_pct = price_data.get('percentchange', 0)
            change_color = "positive" if float(change) >= 0 else "negative"
            st.metric("Change", f"₹{change}", f"{change_pct}%", delta_color="normal")
        with col3:
            st.metric("High", f"₹{price_data.get('high', 'N/A')}")
        with col4:
            st.metric("Low", f"₹{price_data.get('low', 'N/A')}")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Create columns for indicators
    col1, col2, col3 = st.columns(3)
    
    # Organize indicators by category
    trend_indicators = []
    momentum_indicators = []
    volatility_indicators = []
    volume_indicators = []
    
    for indicator in indicators:
        name = indicator.get('name', '')
        if 'MA' in name or 'Moving Average' in name or 'EMA' in name:
            trend_indicators.append(indicator)
        elif 'RSI' in name or 'Stochastic' in name or 'Momentum' in name or 'MACD' in name:
            momentum_indicators.append(indicator)
        elif 'Bollinger' in name or 'ATR' in name or 'Volatility' in name:
            volatility_indicators.append(indicator)
        elif 'Volume' in name or 'OBV' in name:
            volume_indicators.append(indicator)
        else:
            trend_indicators.append(indicator)  # Default to trend
    
    # Display indicators in columns
    with col1:
        st.subheader("Trend Indicators")
        for indicator in trend_indicators:
            with st.expander(f"{indicator.get('name', 'Indicator')}"):
                st.write(f"Value: {indicator.get('value', 'N/A')}")
                st.write(f"Signal: {indicator.get('signal', 'N/A')}")
                st.write(f"Action: {indicator.get('action', 'N/A')}")
    
    with col2:
        st.subheader("Momentum Indicators")
        for indicator in momentum_indicators:
            with st.expander(f"{indicator.get('name', 'Indicator')}"):
                st.write(f"Value: {indicator.get('value', 'N/A')}")
                st.write(f"Signal: {indicator.get('signal', 'N/A')}")
                st.write(f"Action: {indicator.get('action', 'N/A')}")
    
    with col3:
        st.subheader("Volatility & Volume")
        for indicator in volatility_indicators + volume_indicators:
            with st.expander(f"{indicator.get('name', 'Indicator')}"):
                st.write(f"Value: {indicator.get('value', 'N/A')}")
                st.write(f"Signal: {indicator.get('signal', 'N/A')}")
                st.write(f"Action: {indicator.get('action', 'N/A')}")
    
    # Show raw data in expander
    with st.expander("View Raw Data"):
        st.json(data)

# Main app
def main():
    st.title("📈 Stock Technical Indicators Dashboard")
    st.markdown("Get technical analysis indicators for Indian stocks from MoneyControl")
    
    # Load stock symbols
    stock_symbols = load_stock_symbols()
    
    # Search options
    search_option = st.radio("Search by:", ["Symbol", "Multiple Symbols"])
    
    if search_option == "Symbol":
        # Single stock search
        selected_symbol = st.selectbox("Select a stock symbol:", stock_symbols)
        
        if st.button("Get Technical Indicators"):
            with st.spinner(f"Fetching data for {selected_symbol}..."):
                try:
                    # First get ISIN from NSE
                    s = requests.Session()
                    s.get("https://www.nseindia.com/", headers=headers)
                    nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={selected_symbol}"
                    r = s.get(nse_url, headers=headers)
                    
                    if r.status_code == 200:
                        isin = r.json()['metadata']['isin']
                        
                        # Then get sc_id from MoneyControl
                        sc_id, stock_name = get_sc_id(isin)
                        
                        if sc_id:
                            # Finally get technical indicators
                            data = fetch_technical_indicators(sc_id)
                            
                            if data:
                                display_technical_indicators(data, stock_name)
                            else:
                                st.error("Failed to fetch technical indicators.")
                        else:
                            st.error("Could not find stock on MoneyControl.")
                    else:
                        st.error("Failed to fetch ISIN from NSE.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    else:
        # Multiple stock search
        selected_symbols = st.multiselect("Select multiple stock symbols:", stock_symbols)
        
        if st.button("Get Technical Indicators"):
            for symbol in selected_symbols:
                with st.spinner(f"Fetching data for {symbol}..."):
                    try:
                        # First get ISIN from NSE
                        s = requests.Session()
                        s.get("https://www.nseindia.com/", headers=headers)
                        nse_url = f"https://www.nseindia.com/api/quote-equity?symbol={symbol}"
                        r = s.get(nse_url, headers=headers)
                        
                        if r.status_code == 200:
                            isin = r.json()['metadata']['isin']
                            
                            # Then get sc_id from MoneyControl
                            sc_id, stock_name = get_sc_id(isin)
                            
                            if sc_id:
                                # Finally get technical indicators
                                data = fetch_technical_indicators(sc_id)
                                
                                if data:
                                    display_technical_indicators(data, stock_name)
                                else:
                                    st.error(f"Failed to fetch technical indicators for {symbol}.")
                            else:
                                st.error(f"Could not find {symbol} on MoneyControl.")
                        else:
                            st.error(f"Failed to fetch ISIN for {symbol} from NSE.")
                    except Exception as e:
                        st.error(f"An error occurred for {symbol}: {str(e)}")
    
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
