from decimal import Decimal

from hummingbot.data_feed.candles_feed.candles_factory import CandlesFactory
from hummingbot.strategy.directional_strategy_base import DirectionalStrategyBase
from hummingbot.smart_components.position_executor.data_types import PositionConfig, TrailingStop
from hummingbot.core.data_type.common import TradeType

class RSISpot(DirectionalStrategyBase):
    """
    RSI (Relative Strength Index) strategy implementation based on the DirectionalStrategyBase.

    This strategy uses the RSI indicator to generate trading signals and execute trades based on the RSI values.
    It defines the specific parameters and configurations for the RSI strategy.

    Parameters:
        directional_strategy_name (str): The name of the strategy.
        trading_pair (str): The trading pair to be traded.
        exchange (str): The exchange to be used for trading.
        order_amount_usd (Decimal): The amount of the order in USD.
        leverage (int): The leverage to be used for trading.

    Position Parameters:
        stop_loss (float): The stop-loss percentage for the position.
        take_profit (float): The take-profit percentage for the position.
        time_limit (int): The time limit for the position in seconds.
        trailing_stop_activation_delta (float): The activation delta for the trailing stop.
        trailing_stop_trailing_delta (float): The trailing delta for the trailing stop.

    Candlestick Configuration:
        candles (List[CandlesBase]): The list of candlesticks used for generating signals.

    Markets:
        A dictionary specifying the markets and trading pairs for the strategy.

    Methods:
        get_signal(): Generates the trading signal based on the RSI indicator.
        get_processed_df(): Retrieves the processed dataframe with RSI values.
        market_data_extra_info(): Provides additional information about the market data.

    Inherits from:
        DirectionalStrategyBase: Base class for creating directional strategies using the PositionExecutor.
    """
    directional_strategy_name: str = "RSI_spot"
    # Define the trading pair and exchange that we want to use and the csv where we are going to store the entries
    trading_pair: str = "1INCH-USDT"
    exchange: str = "binance"
    order_amount_usd = Decimal("15")
    leverage = 10

    # Configure the parameters for the position
    stop_loss: float = 0.075
    take_profit: float = 1
    time_limit: int = 60 * 55
    trailing_stop_activation_delta = 0.004
    trailing_stop_trailing_delta = 0.001

    candles = [CandlesFactory.get_candle(connector=exchange,
                                         trading_pair=trading_pair,
                                         interval="1m", max_records=150)]
    markets = {exchange: {trading_pair}}

    def get_signal(self):
        """
        Generates the trading signal based on the RSI indicator.
        Returns:
            int: The trading signal (-1 for sell, 0 for hold, 1 for buy).
        """
        candles_df = self.get_processed_df()
        rsi_value = candles_df.iat[-1, -1]
        if rsi_value > 70:
            return -1
        elif rsi_value < 30:
            return 1
        else:
            return 0

    def get_processed_df(self):
        """
        Retrieves the processed dataframe with RSI values.
        Returns:
            pd.DataFrame: The processed dataframe with RSI values.
        """
        candles_df = self.candles[0].candles_df
        candles_df.ta.rsi(length=7, append=True)
        return candles_df

    def market_data_extra_info(self):
        """
        Provides additional information about the market data to the format status.
        Returns:
            List[str]: A list of formatted strings containing market data information.
        """
        lines = []
        columns_to_show = ["timestamp", "open", "low", "high", "close", "volume", "RSI_7"]
        candles_df = self.get_processed_df()
        lines.extend([f"Candles: {self.candles[0].name} | Interval: {self.candles[0].interval}\n"])
        lines.extend(self.candles_formatted_list(candles_df, columns_to_show))
        return lines


    def get_position_config(self):
        signal = self.get_signal()
        if signal == 0:
            return None
        else:
            price = self.connectors[self.exchange].get_mid_price(self.trading_pair)
            side = TradeType.BUY if signal == 1 else TradeType.SELL
            if self.open_order_type.is_limit_type():
                price = price * (1 - signal * self.open_order_slippage_buffer)
                amount = (amount - amount * 0.001) if side == TradeType.SELL else amount
            position_config = PositionConfig(
                timestamp=self.current_timestamp,
                trading_pair=self.trading_pair,
                exchange=self.exchange,
                side=side,
                amount=self.order_amount_usd / price,
                take_profit=self.take_profit,
                stop_loss=self.stop_loss,
                time_limit=self.time_limit,
                entry_price=price,
                open_order_type=self.open_order_type,
                take_profit_order_type=self.take_profit_order_type,
                stop_loss_order_type=self.stop_loss_order_type,
                time_limit_order_type=self.time_limit_order_type,
                trailing_stop=TrailingStop(
                    activation_price_delta=self.trailing_stop_activation_delta,
                    trailing_delta=self.trailing_stop_trailing_delta
                ),
                leverage=self.leverage,
            )
            return position_config