import os
import re
import sys
from pathlib import Path

import pika

AMQP_URL = os.getenv("AMQP_URL", "amqp://festhub:festhub@localhost:5672/")
EXCHANGE = "festhub.events"


def file_order(path):
    digits = re.sub(r"\D", "", path.stem)
    return (int(digits) if digits else 0, path.name)


def main(folder):
    files = sorted(Path(folder).glob("*.json"), key=file_order)
    connection = pika.BlockingConnection(pika.URLParameters(AMQP_URL))
    channel = connection.channel()
    channel.confirm_delivery()
    for path in files:
        properties = pika.BasicProperties(delivery_mode=2, content_type="application/json", message_id=path.name)
        channel.basic_publish(EXCHANGE, "concert.submitted", path.read_bytes(), properties)
    connection.close()
    print(f"published {len(files)} events from {folder}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "event")
