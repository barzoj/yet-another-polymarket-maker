import json
import logging

import websockets

from market_maker import MarketMaker
from market_state import MarketState

logger = logging.getLogger(__name__)

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


async def listen_to_market(
    question_id, market_ids, private_key, funder, min_shares, spread=0.25, order_size=1
):
    logger.info("Starting listening to markets: %s", market_ids)
    state = MarketState(question_id, market_ids[0], market_ids[1])

    async with websockets.connect(WS_URL) as ws:
        logger.info("Connected to Polymarket CLOB WebSocket")

        subscribe_message = json.dumps(
            {
                "type": "market",
                "assets_ids": market_ids,
            }
        )

        res = await ws.send(subscribe_message)
        logger.debug("Subscribed to markets: %s", res)

        market_maker = MarketMaker(private_key, funder, min_shares)

        while True:
            response = await ws.recv()
            event_data = json.loads(response)
            logger.debug("Event data: %s", event_data)

            for event_data in event_data:
                if event_data["event_type"] == "book":
                    logger.debug("order book data: %s", event_data)
                    market_maker.cancel_all_orders()
                    state.on_order_book_event(event_data)
                    orders_info = state.get_state()

                    if orders_info is not None:
                        trade_yes_midpoint = orders_info["trade_yes_midpoint"]
                        trade_no_midpoint = orders_info["trade_no_midpoint"]

                        logger.debug(
                            f"Trade YES midpoint: {trade_yes_midpoint}, Trade NO midpoint: {trade_no_midpoint}"
                        )

                        buy_yes_price = trade_yes_midpoint - spread
                        sell_yes_price = trade_yes_midpoint + spread
                        buy_no_price = trade_no_midpoint - spread
                        sell_no_price = trade_no_midpoint + spread

                        logger.debug(
                            f"Buy YES price:{buy_yes_price}, Sell YES price:{sell_yes_price}, Buy NO price:{buy_no_price}, Sell NO price:{sell_no_price}"
                        )

                        # let's not deal with "extreme" markets
                        if (
                            buy_yes_price < 0.02
                            or buy_no_price < 0.02
                            or sell_no_price > 0.98
                            or sell_yes_price > 0.98
                        ):
                            logger.info("Prices are out of bounds, skipping")
                            continue

                        market_maker.create_order(
                            buy_yes_price,
                            sell_yes_price,
                            market_ids[0],
                            order_size,
                        )
                        market_maker.create_order(
                            buy_no_price,
                            sell_no_price,
                            market_ids[1],
                            order_size,
                        )

                if event_data["event_type"] == "price_change":
                    logger.debug("price change data: %s", event_data)
                    state.on_price_change_event(event_data)
