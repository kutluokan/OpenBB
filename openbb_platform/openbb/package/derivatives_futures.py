### THIS FILE IS AUTO-GENERATED. DO NOT EDIT. ###

import datetime
from typing import List, Literal, Optional, Union

from openbb_core.app.model.field import OpenBBField
from openbb_core.app.model.obbject import OBBject
from openbb_core.app.static.container import Container
from openbb_core.app.static.utils.decorators import exception_handler, validate
from openbb_core.app.static.utils.filters import filter_inputs
from typing_extensions import Annotated


class ROUTER_derivatives_futures(Container):
    """/derivatives/futures
    curve
    historical
    info
    instruments
    """

    def __repr__(self) -> str:
        return self.__doc__ or ""

    @exception_handler
    @validate
    def curve(
        self,
        symbol: Annotated[str, OpenBBField(description="Symbol to get data for.")],
        date: Annotated[
            Union[datetime.date, str, None, List[Union[datetime.date, str, None]]],
            OpenBBField(
                description="A specific date to get data for. Multiple comma separated items allowed for provider(s): cboe, yfinance."
            ),
        ] = None,
        chart: Annotated[
            bool,
            OpenBBField(
                description="Whether to create a chart or not, by default False."
            ),
        ] = False,
        provider: Annotated[
            Optional[Literal["cboe", "deribit", "yfinance"]],
            OpenBBField(
                description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: cboe, deribit, yfinance."
            ),
        ] = None,
        **kwargs
    ) -> OBBject:
        """Futures Term Structure, current or historical.

        Parameters
        ----------
        symbol : str
            Symbol to get data for.
        date : Union[date, str, None, List[Union[date, str, None]]]
            A specific date to get data for. Multiple comma separated items allowed for provider(s): cboe, yfinance.
        chart : bool
            Whether to create a chart or not, by default False.
        provider : Optional[Literal['cboe', 'deribit', 'yfinance']]
            The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: cboe, deribit, yfinance.
        hours_ago : Optional[Union[int, list[int], str]]
            Compare the current curve with the specified number of hours ago. Default is None. Multiple comma separated items allowed. (provider: deribit)

        Returns
        -------
        OBBject
            results : List[FuturesCurve]
                Serializable results.
            provider : Optional[Literal['cboe', 'deribit', 'yfinance']]
                Provider name.
            warnings : Optional[List[Warning_]]
                List of warnings.
            chart : Optional[Chart]
                Chart object.
            extra : Dict[str, Any]
                Extra info.

        FuturesCurve
        ------------
        date : Optional[date]
            The date of the data.
        expiration : str
            Futures expiration month.
        price : Optional[float]
            The price of the futures contract.
        symbol : Optional[str]
            Symbol representing the entity requested in the data. (provider: cboe)
        hours_ago : Optional[int]
            The number of hours ago represented by the price. Only available when hours_ago is set in the query. (provider: deribit)

        Examples
        --------
        >>> from openbb import obb
        >>> obb.derivatives.futures.curve(symbol='VX', provider='cboe', date='2024-06-25')
        >>> obb.derivatives.futures.curve(symbol='NG', provider='yfinance')
        """  # noqa: E501

        return self._run(
            "/derivatives/futures/curve",
            **filter_inputs(
                provider_choices={
                    "provider": self._get_provider(
                        provider,
                        "derivatives.futures.curve",
                        ("cboe", "deribit", "yfinance"),
                    )
                },
                standard_params={
                    "symbol": symbol,
                    "date": date,
                },
                extra_params=kwargs,
                chart=chart,
                info={
                    "symbol": {
                        "deribit": {
                            "multiple_items_allowed": False,
                            "choices": ["BTC", "ETH", "PAXG"],
                        }
                    },
                    "date": {
                        "cboe": {"multiple_items_allowed": True, "choices": None},
                        "yfinance": {"multiple_items_allowed": True, "choices": None},
                    },
                    "hours_ago": {
                        "deribit": {"multiple_items_allowed": True, "choices": None}
                    },
                },
            )
        )

    @exception_handler
    @validate
    def historical(
        self,
        symbol: Annotated[
            Union[str, List[str]],
            OpenBBField(
                description="Symbol to get data for. Multiple comma separated items allowed for provider(s): deribit, yfinance."
            ),
        ],
        start_date: Annotated[
            Union[datetime.date, None, str],
            OpenBBField(description="Start date of the data, in YYYY-MM-DD format."),
        ] = None,
        end_date: Annotated[
            Union[datetime.date, None, str],
            OpenBBField(description="End date of the data, in YYYY-MM-DD format."),
        ] = None,
        expiration: Annotated[
            Optional[str],
            OpenBBField(description="Future expiry date with format YYYY-MM"),
        ] = None,
        chart: Annotated[
            bool,
            OpenBBField(
                description="Whether to create a chart or not, by default False."
            ),
        ] = False,
        provider: Annotated[
            Optional[Literal["deribit", "yfinance"]],
            OpenBBField(
                description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: deribit, yfinance."
            ),
        ] = None,
        **kwargs
    ) -> OBBject:
        """Historical futures prices.

        Parameters
        ----------
        symbol : Union[str, List[str]]
            Symbol to get data for. Multiple comma separated items allowed for provider(s): deribit, yfinance.
        start_date : Union[date, None, str]
            Start date of the data, in YYYY-MM-DD format.
        end_date : Union[date, None, str]
            End date of the data, in YYYY-MM-DD format.
        expiration : Optional[str]
            Future expiry date with format YYYY-MM
        chart : bool
            Whether to create a chart or not, by default False.
        provider : Optional[Literal['deribit', 'yfinance']]
            The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: deribit, yfinance.
        interval : Union[Literal['1m', '3m', '5m', '10m', '15m', '30m', '1h', '2h', '3h', '6h', '12h', '1d'], Literal['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h', '1d', '5d', '1W', '1M', '1Q']]
            Time interval of the data to return. (provider: deribit, yfinance)

        Returns
        -------
        OBBject
            results : List[FuturesHistorical]
                Serializable results.
            provider : Optional[Literal['deribit', 'yfinance']]
                Provider name.
            warnings : Optional[List[Warning_]]
                List of warnings.
            chart : Optional[Chart]
                Chart object.
            extra : Dict[str, Any]
                Extra info.

        FuturesHistorical
        -----------------
        date : datetime
            The date of the data.
        open : float
            The open price.
        high : float
            The high price.
        low : float
            The low price.
        close : float
            The close price.
        volume : float
            The trading volume.
        volume_notional : Optional[float]
            Trading volume in quote currency. (provider: deribit)

        Examples
        --------
        >>> from openbb import obb
        >>> obb.derivatives.futures.historical(symbol='ES', provider='yfinance')
        >>> # Enter multiple symbols.
        >>> obb.derivatives.futures.historical(symbol='ES,NQ', provider='yfinance')
        >>> # Enter expiration dates as "YYYY-MM".
        >>> obb.derivatives.futures.historical(symbol='ES', provider='yfinance', expiration='2025-12')
        """  # noqa: E501

        return self._run(
            "/derivatives/futures/historical",
            **filter_inputs(
                provider_choices={
                    "provider": self._get_provider(
                        provider,
                        "derivatives.futures.historical",
                        ("deribit", "yfinance"),
                    )
                },
                standard_params={
                    "symbol": symbol,
                    "start_date": start_date,
                    "end_date": end_date,
                    "expiration": expiration,
                },
                extra_params=kwargs,
                chart=chart,
                info={
                    "symbol": {
                        "deribit": {"multiple_items_allowed": True, "choices": None},
                        "yfinance": {"multiple_items_allowed": True, "choices": None},
                    },
                    "interval": {
                        "deribit": {
                            "multiple_items_allowed": False,
                            "choices": [
                                "1m",
                                "3m",
                                "5m",
                                "10m",
                                "15m",
                                "30m",
                                "1h",
                                "2h",
                                "3h",
                                "6h",
                                "12h",
                                "1d",
                            ],
                        }
                    },
                },
            )
        )

    @exception_handler
    @validate
    def info(
        self,
        provider: Annotated[
            Optional[Literal["deribit"]],
            OpenBBField(
                description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: deribit."
            ),
        ] = None,
        **kwargs
    ) -> OBBject:
        """Get current trading statistics by futures contract symbol.

        Parameters
        ----------
        provider : Optional[Literal['deribit']]
            The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: deribit.
        symbol : Optional[str]
            Symbol to get data for. Perpetual contracts can be referenced by their currency pair - i.e, SOLUSDC - or by their official Deribit symbol - i.e, SOL_USDC-PERPETUAL For a list of currently available instruments, use `derivatives.futures.instruments()` Multiple comma separated items allowed. (provider: deribit)

        Returns
        -------
        OBBject
            results : List[FuturesInfo]
                Serializable results.
            provider : Optional[Literal['deribit']]
                Provider name.
            warnings : Optional[List[Warning_]]
                List of warnings.
            chart : Optional[Chart]
                Chart object.
            extra : Dict[str, Any]
                Extra info.

        FuturesInfo
        -----------
        symbol : str
            Symbol representing the entity requested in the data.
        state : Optional[Literal['open', 'closed']]
            The state of the order book. Possible values are open and closed. (provider: deribit)
        open_interest : Optional[float]
            The total amount of outstanding contracts in the corresponding amount units. (provider: deribit)
        index_price : Optional[float]
            Current index (reference) price (provider: deribit)
        best_ask_amount : Optional[float]
            It represents the requested order size of all best asks (provider: deribit)
        best_ask_price : Optional[float]
            The current best ask price, null if there aren't any asks (provider: deribit)
        best_bid_price : Optional[float]
            The current best bid price, null if there aren't any bids (provider: deribit)
        best_bid_amount : Optional[float]
            It represents the requested order size of all best bids (provider: deribit)
        last_price : Optional[float]
            The price for the last trade (provider: deribit)
        high : Optional[float]
            Highest price during 24h (provider: deribit)
        low : Optional[float]
            Lowest price during 24h (provider: deribit)
        change_percent : Optional[float]
            24-hour price change expressed as a percentage, null if there weren't any trades (provider: deribit)
        volume : Optional[float]
            Volume during last 24h in base currency (provider: deribit)
        volume_usd : Optional[float]
            Volume in USD (provider: deribit)
        mark_price : Optional[float]
            The mark price for the instrument (provider: deribit)
        settlement_price : Optional[float]
            The settlement price for the instrument. Only when state = open (provider: deribit)
        delivery_price : Optional[float]
            The settlement price for the instrument. Only when state = closed. (provider: deribit)
        estimated_delivery_price : Optional[float]
            Estimated delivery price for the market. (provider: deribit)
        current_funding : Optional[float]
            Current funding (perpetual only) (provider: deribit)
        funding_8h : Optional[float]
            Funding 8h (perpetual only) (provider: deribit)
        interest_value : Optional[float]
            Value used to calculate realized_funding in positions (perpetual only) (provider: deribit)
        max_price : Optional[float]
            The maximum price for the future. Any buy orders submitted higher than this price, will be clamped to this maximum. (provider: deribit)
        min_price : Optional[float]
            The minimum price for the future. Any sell orders submitted lower than this price will be clamped to this minimum. (provider: deribit)
        timestamp : Optional[datetime]
            The timestamp of the data. (provider: deribit)

        Examples
        --------
        >>> from openbb import obb
        >>> obb.derivatives.futures.info(provider='deribit', symbol='BTC')
        >>> obb.derivatives.futures.info(provider='deribit', symbol='SOLUSDC')
        >>> obb.derivatives.futures.info(provider='deribit', symbol='SOL_USDC-PERPETUAL')
        >>> obb.derivatives.futures.info(provider='deribit', symbol='BTC,ETH')
        """  # noqa: E501

        return self._run(
            "/derivatives/futures/info",
            **filter_inputs(
                provider_choices={
                    "provider": self._get_provider(
                        provider,
                        "derivatives.futures.info",
                        ("deribit",),
                    )
                },
                standard_params={},
                extra_params=kwargs,
                info={
                    "symbol": {
                        "deribit": {"multiple_items_allowed": True, "choices": None}
                    }
                },
            )
        )

    @exception_handler
    @validate
    def instruments(
        self,
        provider: Annotated[
            Optional[Literal["deribit"]],
            OpenBBField(
                description="The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: deribit."
            ),
        ] = None,
        **kwargs
    ) -> OBBject:
        """Get reference data for available futures instruments by provider.

        Parameters
        ----------
        provider : Optional[Literal['deribit']]
            The provider to use, by default None. If None, the priority list configured in the settings is used. Default priority: deribit.

        Returns
        -------
        OBBject
            results : List[FuturesInstruments]
                Serializable results.
            provider : Optional[Literal['deribit']]
                Provider name.
            warnings : Optional[List[Warning_]]
                List of warnings.
            chart : Optional[Chart]
                Chart object.
            extra : Dict[str, Any]
                Extra info.

        FuturesInstruments
        ------------------
        instrument_id : Optional[int]
            Deribit Instrument ID (provider: deribit)
        symbol : Optional[str]
            Symbol representing the entity requested in the data. (provider: deribit)
        base_currency : Optional[str]
            The underlying currency being traded. (provider: deribit)
        counter_currency : Optional[str]
            Counter currency for the instrument. (provider: deribit)
        quote_currency : Optional[str]
            The currency in which the instrument prices are quoted. (provider: deribit)
        settlement_currency : Optional[str]
            Settlement currency for the instrument. (provider: deribit)
        future_type : Optional[str]
            Type of the instrument. linear or reversed (provider: deribit)
        settlement_period : Optional[str]
            The settlement period. (provider: deribit)
        price_index : Optional[str]
            Name of price index that is used for this instrument (provider: deribit)
        contract_size : Optional[float]
            Contract size for instrument. (provider: deribit)
        is_active : Optional[bool]
            Indicates if the instrument can currently be traded. (provider: deribit)
        creation_timestamp : Optional[datetime]
            The time when the instrument was first created (milliseconds since the UNIX epoch). (provider: deribit)
        expiration_timestamp : Optional[datetime]
            The time when the instrument will expire (milliseconds since the UNIX epoch). (provider: deribit)
        tick_size : Optional[float]
            Specifies minimal price change and, as follows, the number of decimal places for instrument prices. (provider: deribit)
        min_trade_amount : Optional[float]
            Minimum amount for trading, in USD units. (provider: deribit)
        max_leverage : Optional[int]
            Maximal leverage for instrument. (provider: deribit)
        max_liquidation_commission : Optional[float]
            Maximal liquidation trade commission for instrument. (provider: deribit)
        block_trade_commission : Optional[float]
            Block Trade commission for instrument. (provider: deribit)
        block_trade_min_trade_amount : Optional[float]
            Minimum amount for block trading. (provider: deribit)
        block_trade_tick_size : Optional[float]
            Specifies minimal price change for block trading. (provider: deribit)
        maker_commission : Optional[float]
            Maker commission for instrument. (provider: deribit)
        taker_commission : Optional[float]
            Taker commission for instrument. (provider: deribit)

        Examples
        --------
        >>> from openbb import obb
        >>> obb.derivatives.futures.instruments(provider='deribit')
        """  # noqa: E501

        return self._run(
            "/derivatives/futures/instruments",
            **filter_inputs(
                provider_choices={
                    "provider": self._get_provider(
                        provider,
                        "derivatives.futures.instruments",
                        ("deribit",),
                    )
                },
                standard_params={},
                extra_params=kwargs,
            )
        )
