### THIS FILE IS AUTO-GENERATED. DO NOT EDIT. ###


from openbb_core.app.static.container import Container


class Extensions(Container):
    # fmt: off
    """
Routers:
    /commodity
    /crypto
    /currency
    /derivatives
    /econometrics
    /economy
    /equity
    /etf
    /fixedincome
    /index
    /news
    /quantitative
    /regulators
    /technical

Extensions:
    - commodity@1.3.0
    - crypto@1.4.0
    - currency@1.4.0
    - derivatives@1.4.0
    - econometrics@1.5.0
    - economy@1.4.0
    - equity@1.4.0
    - etf@1.4.0
    - fixedincome@1.4.1
    - index@1.4.0
    - news@1.4.0
    - quantitative@1.4.0
    - regulators@1.4.0
    - technical@1.4.0

    - alpha_vantage@1.4.0
    - benzinga@1.4.0
    - biztoc@1.4.0
    - bls@1.1.0
    - cboe@1.4.0
    - cftc@1.1.0
    - deribit@1.0.0
    - ecb@1.4.0
    - econdb@1.3.0
    - federal_reserve@1.4.0
    - finra@1.4.0
    - finviz@1.3.0
    - fmp@1.4.0
    - fred@1.4.0
    - government_us@1.4.0
    - imf@1.1.0
    - intrinio@1.4.0
    - multpl@1.1.0
    - nasdaq@1.4.0
    - oecd@1.4.0
    - polygon@1.4.0
    - sec@1.4.0
    - seeking_alpha@1.4.0
    - stockgrid@1.4.0
    - tiingo@1.4.0
    - tmx@1.3.0
    - tradier@1.3.0
    - tradingeconomics@1.4.0
    - us_eia@1.1.0
    - wsj@1.4.0
    - yfinance@1.4.0    """
    # fmt: on

    def __repr__(self) -> str:
        return self.__doc__ or ""

    @property
    def commodity(self):
        # pylint: disable=import-outside-toplevel
        from . import commodity

        return commodity.ROUTER_commodity(command_runner=self._command_runner)

    @property
    def crypto(self):
        # pylint: disable=import-outside-toplevel
        from . import crypto

        return crypto.ROUTER_crypto(command_runner=self._command_runner)

    @property
    def currency(self):
        # pylint: disable=import-outside-toplevel
        from . import currency

        return currency.ROUTER_currency(command_runner=self._command_runner)

    @property
    def derivatives(self):
        # pylint: disable=import-outside-toplevel
        from . import derivatives

        return derivatives.ROUTER_derivatives(command_runner=self._command_runner)

    @property
    def econometrics(self):
        # pylint: disable=import-outside-toplevel
        from . import econometrics

        return econometrics.ROUTER_econometrics(command_runner=self._command_runner)

    @property
    def economy(self):
        # pylint: disable=import-outside-toplevel
        from . import economy

        return economy.ROUTER_economy(command_runner=self._command_runner)

    @property
    def equity(self):
        # pylint: disable=import-outside-toplevel
        from . import equity

        return equity.ROUTER_equity(command_runner=self._command_runner)

    @property
    def etf(self):
        # pylint: disable=import-outside-toplevel
        from . import etf

        return etf.ROUTER_etf(command_runner=self._command_runner)

    @property
    def fixedincome(self):
        # pylint: disable=import-outside-toplevel
        from . import fixedincome

        return fixedincome.ROUTER_fixedincome(command_runner=self._command_runner)

    @property
    def index(self):
        # pylint: disable=import-outside-toplevel
        from . import index

        return index.ROUTER_index(command_runner=self._command_runner)

    @property
    def news(self):
        # pylint: disable=import-outside-toplevel
        from . import news

        return news.ROUTER_news(command_runner=self._command_runner)

    @property
    def quantitative(self):
        # pylint: disable=import-outside-toplevel
        from . import quantitative

        return quantitative.ROUTER_quantitative(command_runner=self._command_runner)

    @property
    def regulators(self):
        # pylint: disable=import-outside-toplevel
        from . import regulators

        return regulators.ROUTER_regulators(command_runner=self._command_runner)

    @property
    def technical(self):
        # pylint: disable=import-outside-toplevel
        from . import technical

        return technical.ROUTER_technical(command_runner=self._command_runner)
