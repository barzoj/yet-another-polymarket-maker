import argparse
import asyncio
import logging

from market_events_processor import listen_to_market


def main():
    parser = argparse.ArgumentParser(description="Polygon trading script")

    parser.add_argument(
        "-v", "--verbose", choices=["DEBUG", "INFO", "ERROR"], help="set logging level"
    )
    parser.add_argument(
        "-q", "--question-id", required=True, help="id of a question", type=str
    )
    parser.add_argument(
        "-y", "--yes-token-id", required=True, help="id of yes token", type=str
    )
    parser.add_argument(
        "-n", "--no-token-id", required=True, help="id of no token", type=str
    )
    parser.add_argument(
        "-s",
        "--spread",
        type=float,
        default=0.025,
        help="spread to maintain, default is 0.025",
    )
    parser.add_argument(
        "-o",
        "--order-size",
        type=int,
        required=False,
        help="multiplier of min_shares to trade",
        default=1,
    )

    parser.add_argument(
        "-m",
        "--min-shares",
        type=int,
        required=True,
        help="min amount of shares to open a position",
    )

    parser.add_argument(
        "-p",
        "--private-key",
        required=True,
        help="polymarket private key",
    )

    parser.add_argument(
        "-f",
        "--funder",
        required=True,
        help="funder address",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=getattr(logging, args.verbose))
    else:
        logging.basicConfig(level=logging.INFO)

    while True:
        try:
            asyncio.run(
                listen_to_market(
                    args.question_id,
                    [args.yes_token_id, args.no_token_id],
                    spread=args.spread,
                    order_size=args.order_size,
                    private_key=args.private_key,
                    funder=args.funder,
                    min_shares=args.min_shares,
                )
            )
        except Exception as e:
            logging.error(f"Connection lost: {e}")


if __name__ == "__main__":
    main()
