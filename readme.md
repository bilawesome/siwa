## Siwa Oracle 

## OVERVIEW:
    This code base provides a CLI for running and interacting various data production algorithms which are then collected by another service and saved to the blockchain. 

## Setup:
    You should run `pip install -r requirements.txt`

    You should also run setup.py to install sentiment analysis data for the twitter sentiment analyzer.

    Each feed may itself require separate setup. 
    See the /feeds directory and the readme.md files therein

## Files:
* `siwa.py` - provides CLI interface / thread handling
* `siwa_logging.py` log handler to log to SQLite
* `endpoint.py` http/json endpoint, run automatically via siwa CLI, or standalone
* `all_feeds.py` - all enabled datafeeds from `feeds/`
* `feeds/data_feed.py` - defines class structure shared by all datafeeds
* `feeds/*.py` - e.g. `gauss.py` - defines an individual datafeed

## Examples:
    endpoint example: http://127.0.0.1:16556/datafeed/gauss
    (you may need to pre-populate by running gauss for a second)

## Datafeed Notes:
* Twitter datafeed returns (as a datapoint) an "average-of-past-5-tweets" sentiment value between -1 and +1 (totally negative to totally positive), currently this means if following more than one username or term, the sentiment would be averaged across the most recent 5 tweets from everything followed -- this could later be modified to create separate data for separate users, or to consider an average-of-averages (5 tweets per user/hashtag/term, instead of 5 tweets total)

## Datafeed IDs:
* 1 gauss -> gauss
* 2 crypto_indices -> MCAP1000
* 3 stablecoins -> USDC
* 4 stablecoins -> BUSD
* 5 stablecoins -> Tether
* 6 stablecoins -> DAI
* 7 Twitter -> sentiment per user ID per last n tweets

## Monitoring Architecture
The monitoring architecture for Siwa/Overlay comprises of three services: Grafana, Grafana Loki, and Promtail, each of which are described below. These three are configured in the docker-compose.yml file.

### Grafana 
    - Dashboarding and data visualization tool
    - Open-source
    - Allows you to query, visualize, and alert on data coming from various sources
    - Allows sending to telegram, discord, email
    - Allows creating Alert Rules based on user-specified conditions
    - Pulls data from multiple data sources (e.g. Loki, Prometheus)

### Grafana Loki
    - Logs aggregation tool 
    - Open-source
    - Multi-tenant
    - LogQL - query language for Loki

### Promtail
    - agent/client that pushes logs to Loki
    - Scrapes logs from apps and pushes them to Loki
    - in this repot, scrape configuration is defined in promtail-config.yml file

### Run the monitoring architecture with docker
```
docker-compose up
```
