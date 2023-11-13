from prometheus_client import (
    CollectorRegistry,
    Gauge,
)

csgo_index_gauge = Gauge(
    'csgo_index',
    'CSGO Skins Index'
)
csgo_price_gauge = Gauge(
    'csgo_price',
    'CSGO Skins Price',
    ['market_hash_name']
)

registry = CollectorRegistry()
registry.register(csgo_index_gauge)
