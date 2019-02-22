from http.client import HTTPSConnection, HTTPResponse
from argparse import ArgumentParser
import json
import logging
from json import JSONDecodeError


logger = logging.getLogger(__name__)


class RateClientError(Exception):
    pass


class RateClient:
    def get_rate(self) -> float:
        logger.debug("Sending request")
        response = self.send_request()
        logger.debug("Received response")
        code = response.code
        if code != 200:
            message = f"{code}: {response.reason}"
            raise RateClientError(message)
        return self.parse_response(response)

    def send_request(self) -> HTTPResponse:
        raise NotImplementedError

    def parse_response(self, response: HTTPResponse) -> float:
        raise NotImplementedError


class RatesApiClient(RateClient):
    domain = "ratesapi.io"

    def send_request(self) -> HTTPResponse:
        connection = HTTPSConnection(self.domain)
        connection.request("GET", "/api/latest/?symbols=RUB&base=USD")
        return connection.getresponse()

    def parse_response(self, response: HTTPResponse) -> float:
        try:
            data = json.load(response)
        except JSONDecodeError:
            message = "Invalid response body"
            raise RateClientError(message)
        rates = data.get("rates", {})
        rate = rates.get("RUB", None)
        if rate is None:
            message = f"The \"{self.domain}\" server has changed response format. Received: {data}"
            raise RateClientError(message)
        return rate


class CurrencyConverter:
    def __init__(self, client: RateClient):
        self.client = client

    def convert(self, amount: float) -> float:
        rate = self.client.get_rate()
        logger.debug("Got exchange rate %s", rate)
        return amount * rate


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("amount", help="Amount of rubles for conversion to dollars", type=float)
    parser.add_argument("--logfile", help="Log file", default="log.log")
    args = parser.parse_args()
    logging.basicConfig(filename=args.logfile, level=logging.DEBUG)
    rate_client = RatesApiClient()
    converter = CurrencyConverter(rate_client)
    try:
        dollars = converter.convert(args.amount)
        print(f"{dollars:0.2f}")
    except RateClientError as e:
        print(e)
        logger.exception(str(e))
