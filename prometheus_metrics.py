from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

csgo_index_gauge = Gauge('csgo_index', 'CSGO Skins Index')

registry = CollectorRegistry()
registry.register(csgo_index_gauge)
