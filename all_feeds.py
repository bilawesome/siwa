# from feeds.gauss import gauss
from feeds.crypto_indices import mcap1000, memecoins
from feeds.stablecoins import stablecoins as s
from feeds import test_feed
from feeds.twitter import twitter

Test = test_feed.Test
# Gauss = gauss.Gauss
MCAP1000, MemeCoins = mcap1000.MCAP1000, memecoins.MemeCoins
USDC, BUSD, Tether, Dai = s.USDC, s.BUSD, s.Tether, s.Dai
Twitter = twitter.Twitter

# NOTE: this is a dict of all feed classes that SIWA can run, keyed by feed name
#     this is used in endpoint.py to route requests to the correct feed
#
# TO ENABLE OR DISABLE A FEED, ADD OR REMOVE IT FROM THIS DICT
all_feeds = {
    # Gauss.NAME: Gauss,
    Test.NAME: Test,
    MCAP1000.NAME: MCAP1000,
    MemeCoins.NAME: MemeCoins,
    USDC.NAME: USDC,
    BUSD.NAME: BUSD,
    Tether.NAME: Tether,
    Dai.NAME: Dai,
    Twitter.NAME: Twitter,
}
