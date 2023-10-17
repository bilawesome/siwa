import unittest
import pandas as pd
from unittest.mock import patch, Mock
from apis import csgoskins


class TestCSGOSkins(unittest.TestCase):

    def get_sample_data(self):
        # Get sample data from file
        with open('test/sample_data/csgoskins_data.json', 'r') as f:
            return f.read()

    def setUp(self):
        self.csgo = csgoskins.CSGOSkins()
        self.sample_data = self.get_sample_data()

    @patch('requests.request')
    def test_get_prices(self, mock_request):
        mock_request.return_value.json.return_value = self.sample_data
        response = self.csgo.get_prices()
        self.assertEqual(response, self.sample_data)

    def test_get_prices_df(self):
        sample_data = self.csgo.get_prices()
        expected_df = pd.json_normalize(
            sample_data[self.csgo.DATA_KEY],
            record_path=[self.csgo.PRICES_KEY],
            meta=self.csgo.MARKET_HASH_NAME_KEY
        )
        expected_df[self.csgo.PRICE_KEY] =\
            expected_df[self.csgo.PRICE_KEY]/100
        actual_df = self.csgo.get_prices_df()

        self.assertIsInstance(actual_df, pd.DataFrame)
        self.assertGreater(len(actual_df), 0)
        pd.testing.assert_frame_equal(actual_df, expected_df)

    def test_agg_data(self):
        df = self.csgo.get_prices_df()
        agg_df = self.csgo.agg_data(df)
        self.assertNotEqual(len(agg_df), len(df))
        self.assertIn('price', agg_df.columns)
        self.assertIn('quantity', agg_df.columns)

    def test_get_caps(self):
        df = pd.DataFrame({
            'market_hash_name': ['item1', 'item2'],
            'avg_index_share': [0.5, 0.3],
            'std_index_share': [0.1, 0.05]
        })
        caps = self.csgo.get_caps(df, k=0.1)
        self.assertIn('upper_cap_index_share', caps.columns)
        self.assertIn('lower_cap_index_share', caps.columns)

    def test_adjust_share(self):
        df = pd.DataFrame({
            'index': [100, 200, 300],
            'lower_cap_index_share': [0.2, 0.3, 0.5],
            'upper_cap_index_share': [0.3, 0.4, 0.6]
        })
        adjusted_df = self.csgo.adjust_share(df, 100)
        self.assertEqual(len(df), len(adjusted_df))

    @patch('web3.eth.Eth.contract')
    def test_cap_compared_to_prev(self, mock_contract):
        mock_contract_instance = Mock()
        mock_contract_instance.functions.latestAnswer().call.return_value = 100
        mock_contract_instance.functions.decimals().call.return_value = 2
        mock_contract.return_value = mock_contract_instance
        capped_value = self.csgo.cap_compared_to_prev(110)
        self.assertEqual(capped_value, 1.05)

    def test_get_index(self):
        df = self.csgo.get_prices_df()
        caps = self.csgo.get_caps(df, k=0.1)
        index = self.csgo.get_index(df, caps)
        self.assertIsInstance(index, float)

if __name__ == '__main__':
    unittest.main()
