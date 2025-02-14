import logging

logger = logging.getLogger(__name__)


class MarketState(object):
    def __init__(self, market_id, trade_yes_id, trade_no_id):
        self.market_id = market_id
        self.trade_yes_id = trade_yes_id
        self.trade_no_id = trade_no_id
        self.trade_yes_bids = []
        self.trade_yes_asks = []
        self.trade_no_bids = []
        self.trade_no_asks = []

    def on_order_book_event(self, data):
        logger.debug(f"on_order_book_event: {data}")

        # sanity check first
        if "event_type" in data and data["event_type"] != "book":
            logger.error("invalid event type")
            raise ValueError("invalid event type")

        # TODO: market_id sanity check

        asset_matched = False
        if data["asset_id"] == self.trade_yes_id:
            asset_matched = True
            logger.debug(f"yes asset matched, asset_id: {self.trade_yes_id}")
            self.trade_yes_bids = sorted(
                data.get("bids", []), key=lambda x: float(x["price"]), reverse=True
            )

            self.trade_yes_asks = sorted(
                data.get("asks", []), key=lambda x: float(x["price"]), reverse=False
            )

        if data["asset_id"] == self.trade_no_id:
            asset_matched = True
            logger.debug(f"no asset matched, asset_id: {self.trade_no_id}")
            self.trade_no_bids = sorted(
                data.get("bids", []), key=lambda x: float(x["price"]), reverse=True
            )

            self.trade_no_asks = sorted(
                data.get("asks", []), key=lambda x: float(x["price"]), reverse=False
            )

        if not asset_matched:
            logger.error("invalid asset id")
            raise ValueError("invalid asset id")

    def __apply_price_change(self, data, trade_ask, trade_bid):
        logger.debug(f"__apply_price_change: {data}")
        for change in data["changes"]:
            price = float(change["price"])
            if change["side"] == "BUY":
                # update the bid price. first, check if the price already exists
                for bid in trade_ask:
                    if float(bid["price"]) == price:
                        bid["size"] = change["size"]
                        break
                else:
                    # if the price doesn't exist, add it
                    trade_ask.append({"price": price, "size": change["size"]})
                    # sort the bids by price
                    trade_ask = sorted(
                        trade_ask,
                        key=lambda x: float(x["price"]),
                        reverse=True,
                    )

            if change["side"] == "SELL":
                # update the sell price. first, check if the price already exists
                for bid in trade_bid:
                    if float(bid["price"]) == price:
                        bid["size"] = change["size"]
                        break
                else:
                    # if the price doesn't exist, add it
                    trade_bid.append({"price": price, "size": change["size"]})
                    # sort the bids by price
                    trade_bid = sorted(
                        trade_bid,
                        key=lambda x: float(x["price"]),
                        reverse=True,
                    )

        return trade_ask, trade_bid

    def on_price_change_event(self, data):
        logger.debug(f"on_price_change_event: {data}")
        asset_matched = False
        if data["asset_id"] == self.trade_yes_id:
            asset_matched = True
            self.trade_yes_asks, self.trade_yes_bids = self.__apply_price_change(
                trade_ask=self.trade_yes_asks, trade_bid=self.trade_yes_bids, data=data
            )

        if data["asset_id"] == self.trade_no_id:
            asset_matched = True
            self.trade_no_asks, self.trade_no_bids = self.__apply_price_change(
                trade_ask=self.trade_no_asks, trade_bid=self.trade_no_bids, data=data
            )

        if not asset_matched:
            logger.error("invalid asset id")
            raise ValueError("invalid asset id")

    def get_state(self):
        logger.debug("fetching market state")
        if (
            not self.trade_no_asks
            or not self.trade_no_bids
            or not self.trade_yes_asks
            or not self.trade_yes_bids
        ):
            logger.info("not enough data to provide state")
            return None

        best_trade_yes_bid = float(self.trade_yes_bids[0]["price"])
        best_trade_yes_ask = float(self.trade_yes_asks[0]["price"])
        best_trade_no_bid = float(self.trade_no_bids[0]["price"])
        best_trade_no_ask = float(self.trade_no_asks[0]["price"])

        trade_yes_midpoint = (best_trade_yes_bid + best_trade_yes_ask) / 2

        trade_yes_spread = best_trade_yes_ask - best_trade_yes_bid

        trade_no_midpoint = (best_trade_no_bid + best_trade_no_ask) / 2

        trade_no_spread = best_trade_no_ask - best_trade_no_bid

        return {
            "trade_yes_midpoint": trade_yes_midpoint,
            "trade_yes_spread": trade_yes_spread,
            "trade_no_midpoint": trade_no_midpoint,
            "trade_no_spread": trade_no_spread,
        }

