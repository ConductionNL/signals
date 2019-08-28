from signals.apps.reporting.indicators.n_melding_nieuw import NMeldingNieuw
from signals.apps.reporting.indicators.n_melding_open import NMeldingOpen


def derive_routes(indicators):
    routes = {}

    for indicator in indicators:
        routes[indicator.code] = indicator
    return routes


INDICATOR_ROUTES = derive_routes([
    NMeldingNieuw,
    NMeldingOpen,
])
