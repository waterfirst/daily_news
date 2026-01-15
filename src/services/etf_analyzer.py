"""
ETF Analysis Service for Daily Automated Intelligence Platform (DAIP)
Analyzes Korean ETFs and provides investment recommendations
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
from dataclasses import dataclass, asdict

from src.config import settings, ETFConfig
from src.logger import setup_logger
from src.telegram_bot import get_telegram_bot

logger = setup_logger("daip.etf")


@dataclass
class ETFData:
    """ETF data structure"""
    ticker: str
    name: str
    current_price: float
    change_pct: float
    volume: int
    stochastic_k: float
    stochastic_d: float
    signal: str  # BUY, SELL, HOLD, WATCH
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class ETFAnalyzer:
    """ETF analysis and recommendation service"""

    def __init__(self):
        """Initialize ETF analyzer"""
        self.tickers = ETFConfig.ETF_TICKERS
        self.lookback_days = ETFConfig.LOOKBACK_DAYS
        self.stochastic_period = ETFConfig.STOCHASTIC_PERIOD
        self.oversold_threshold = ETFConfig.OVERSOLD_THRESHOLD
        self.overbought_threshold = ETFConfig.OVERBOUGHT_THRESHOLD
        self.top_n = ETFConfig.TOP_N_RECOMMENDATIONS

        self.telegram_bot = get_telegram_bot()
        logger.info("ETF Analyzer initialized")

    def calculate_stochastic(self, df: pd.DataFrame, period: int = 14) -> tuple:
        """
        Calculate Stochastic oscillator (%K and %D)

        Args:
            df: DataFrame with OHLC data
            period: Stochastic period

        Returns:
            Tuple of (%K, %D) values
        """
        try:
            # Calculate %K
            low_min = df['Low'].rolling(window=period).min()
            high_max = df['High'].rolling(window=period).max()

            stoch_k = 100 * (df['Close'] - low_min) / (high_max - low_min)

            # Calculate %D (3-day SMA of %K)
            stoch_d = stoch_k.rolling(window=3).mean()

            return stoch_k.iloc[-1], stoch_d.iloc[-1]
        except Exception as e:
            logger.error(f"Error calculating stochastic: {str(e)}")
            return 50.0, 50.0  # Return neutral values

    def get_etf_data(self, ticker: str) -> Optional[ETFData]:
        """
        Get ETF data and calculate indicators

        Args:
            ticker: ETF ticker symbol

        Returns:
            ETFData object or None if failed
        """
        try:
            # Download historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)

            logger.debug(f"Fetching data for {ticker}")
            etf = yf.Ticker(ticker)
            df = etf.history(start=start_date, end=end_date)

            if df.empty:
                logger.warning(f"No data available for {ticker}")
                return None

            # Get current price and change
            current_price = df['Close'].iloc[-1]
            prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
            change_pct = ((current_price - prev_price) / prev_price) * 100
            volume = int(df['Volume'].iloc[-1])

            # Calculate stochastic
            stoch_k, stoch_d = self.calculate_stochastic(df, self.stochastic_period)

            # Determine signal
            signal = self._determine_signal(stoch_k, stoch_d, change_pct)

            # Get ETF name
            name = etf.info.get('longName', ticker)

            etf_data = ETFData(
                ticker=ticker,
                name=name,
                current_price=float(current_price),
                change_pct=float(change_pct),
                volume=volume,
                stochastic_k=float(stoch_k),
                stochastic_d=float(stoch_d),
                signal=signal,
                timestamp=datetime.now()
            )

            logger.debug(f"Retrieved data for {ticker}: {signal}")
            return etf_data

        except Exception as e:
            logger.error(f"Error fetching data for {ticker}: {str(e)}")
            return None

    def _determine_signal(self, stoch_k: float, stoch_d: float, change_pct: float) -> str:
        """
        Determine buy/sell/hold signal based on indicators

        Args:
            stoch_k: Stochastic %K value
            stoch_d: Stochastic %D value
            change_pct: Price change percentage

        Returns:
            Signal string (BUY, SELL, HOLD, WATCH)
        """
        # Oversold + bullish crossover = BUY
        if stoch_k < self.oversold_threshold and stoch_k > stoch_d:
            return "BUY"

        # Overbought + bearish crossover = SELL
        if stoch_k > self.overbought_threshold and stoch_k < stoch_d:
            return "SELL"

        # Moderate levels + positive momentum = WATCH
        if 40 < stoch_k < 60 and change_pct > 0:
            return "WATCH"

        return "HOLD"

    def analyze_all_etfs(self) -> List[ETFData]:
        """
        Analyze all configured ETFs

        Returns:
            List of ETFData objects
        """
        logger.info(f"Analyzing {len(self.tickers)} ETFs")
        results = []

        for ticker in self.tickers:
            etf_data = self.get_etf_data(ticker)
            if etf_data:
                results.append(etf_data)

        logger.info(f"Successfully analyzed {len(results)} ETFs")
        return results

    def get_recommendations(self) -> List[ETFData]:
        """
        Get top ETF recommendations

        Returns:
            List of recommended ETFs sorted by signal strength
        """
        all_etfs = self.analyze_all_etfs()

        if not all_etfs:
            logger.warning("No ETF data available for recommendations")
            return []

        # Sort by signal priority and change percentage
        signal_priority = {"BUY": 4, "WATCH": 3, "HOLD": 2, "SELL": 1}

        sorted_etfs = sorted(
            all_etfs,
            key=lambda x: (signal_priority.get(x.signal, 0), x.change_pct),
            reverse=True
        )

        recommendations = sorted_etfs[:self.top_n]

        logger.info(f"Generated {len(recommendations)} recommendations")
        return recommendations

    def run(self) -> bool:
        """
        Run ETF analysis and send report

        Returns:
            True if successful
        """
        try:
            logger.info("Starting ETF analysis run")

            # Get recommendations
            recommendations = self.get_recommendations()

            if not recommendations:
                logger.warning("No recommendations generated")
                return False

            # Convert to dict format for Telegram
            etf_data_list = [
                {
                    'ticker': etf.ticker,
                    'name': etf.name,
                    'change_pct': etf.change_pct,
                    'stochastic': etf.stochastic_k,
                    'signal': etf.signal
                }
                for etf in recommendations
            ]

            # Send via Telegram
            success = self.telegram_bot.send_etf_report(
                etf_data_list,
                timestamp=datetime.now()
            )

            if success:
                logger.info("ETF report sent successfully")
            else:
                logger.error("Failed to send ETF report")

            return success

        except Exception as e:
            logger.error(f"ETF analysis run failed: {str(e)}")
            self.telegram_bot.send_error_notification(
                "ETF Analyzer",
                str(e)
            )
            return False


# Service instance
_etf_analyzer: Optional[ETFAnalyzer] = None


def get_etf_analyzer() -> ETFAnalyzer:
    """Get or create ETF analyzer instance"""
    global _etf_analyzer
    if _etf_analyzer is None:
        _etf_analyzer = ETFAnalyzer()
    return _etf_analyzer


def run_etf_analysis() -> None:
    """Run ETF analysis (for scheduler)"""
    analyzer = get_etf_analyzer()
    analyzer.run()


# Example usage
if __name__ == "__main__":
    # Test ETF analyzer
    analyzer = ETFAnalyzer()

    # Get single ETF data
    etf_data = analyzer.get_etf_data("069500.KS")
    if etf_data:
        logger.info(f"ETF Data: {etf_data}")

    # Get recommendations
    recommendations = analyzer.get_recommendations()
    for rec in recommendations:
        logger.info(f"{rec.name}: {rec.signal} (Change: {rec.change_pct:.2f}%)")

    # Run full analysis
    analyzer.run()
