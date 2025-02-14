import logging

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.constants import POLYGON
from py_clob_client.order_builder.constants import BUY

log = logging.getLogger(__name__)


class MarketMaker(object):
    host = "https://clob.polymarket.com"
    chain_id = POLYGON

    def __init__(self, key, funder, min_shares):
        self.key = key
        self.funder = funder
        self.min_shares = min_shares

        self.client = ClobClient(
            self.host,
            key=self.key,
            chain_id=self.chain_id,
            signature_type=1,
            funder=self.funder,
        )
        self.client.set_api_creds(self.client.create_or_derive_api_creds())
        log.info("Polymarket market maker initialized")

    def cancel_all_orders(self):
        log.info("Cancelling all orders")
        self.client.cancel_all()

    def create_order(self, buy_price, sell_price, token_id, size):
        try:
            log.debug(
                f"Creating buy/sell orders for {token_id} buy_price: {buy_price}, sell_price: {sell_price} size: {size}"
            )
            buy_order = self.client.create_and_post_order(
                OrderArgs(
                    price=buy_price,
                    size=self.min_shares * size,
                    side=BUY,
                    token_id=token_id,
                )
            )
            log.info(f"Created buy order: {buy_order}")
        except Exception as e:
            log.error(f"Error creating buy/sell orders: {e}")
            return
