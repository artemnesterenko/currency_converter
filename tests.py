import json
import unittest
from io import StringIO
from unittest.mock import patch, Mock

from currency_converter import RateClient, CurrencyConverter, RatesApiClient, RateClientError


class TestCurrencyConverter(unittest.TestCase):

    def test_convert(self):
        rate = 30
        with patch.object(RateClient, "get_rate", return_value=rate):
            client = RateClient()
            converter = CurrencyConverter(client)
            amount = 2
            self.assertEqual(converter.convert(amount), amount * rate)


class TestRateClient(unittest.TestCase):
    def test_success_code(self):
        response = Mock()
        response.code = 200
        with patch.object(RateClient, "send_request", return_value=response),\
             patch.object(RateClient, "parse_response") as parse_mock:
            client = RateClient()
            client.get_rate()
            parse_mock.assert_called_once_with(response)

    def test_non_success_code(self):
        response = Mock()
        response.code = 400
        with patch.object(RateClient, "send_request", return_value=response):
            client = RateClient()
            with self.assertRaises(RateClientError):
                client.get_rate()


class TestRatesApiClient(unittest.TestCase):

    def test_parse_invalid_response(self):
        client = RatesApiClient()
        response = StringIO("There is no json for you")
        with self.assertRaises(RateClientError):
            client.parse_response(response)

    def test_changed_format(self):
        client = RatesApiClient()
        response = StringIO("{\"key\": \"value\"}")
        with self.assertRaises(RateClientError):
            client.parse_response(response)

    def test_correct_response(self):
        client = RatesApiClient()
        rate = 1
        response_body = {
            "rates": {
                "RUB": rate
            }
        }
        response = StringIO(json.dumps(response_body))
        parsed_rate = client.parse_response(response)
        self.assertEqual(rate, parsed_rate)


if __name__ == '__main__':
    unittest.main()
