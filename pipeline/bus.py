import json
import logging
import os
import time

import grpc
import pika

from cli_api import FestHubError

AMQP_URL = os.getenv("AMQP_URL", "amqp://festhub:festhub@localhost:5672/")
EXCHANGE = "festhub.events"
RETRY_CODES = {grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.DEADLINE_EXCEEDED}


def reject(channel, method, name, reason):
    logging.warning("%s: sent to dead letter queue: %s", name, reason)
    channel.basic_nack(method.delivery_tag, requeue=False)


def run(queue, handle, emits=None):
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(message)s")
    logging.getLogger("pika").setLevel(logging.WARNING)
    channel = pika.BlockingConnection(pika.URLParameters(AMQP_URL)).channel()
    channel.confirm_delivery()
    channel.basic_qos(prefetch_count=1)

    def on_message(channel, method, properties, body):
        name = properties.message_id or "message"
        try:
            outgoing = handle(json.loads(body))
        except FestHubError as error:
            if error.code not in RETRY_CODES:
                return reject(channel, method, name, error)
            logging.warning("%s: %s, retrying", name, error)
            time.sleep(1)
            return channel.basic_nack(method.delivery_tag, requeue=True)
        except KeyError as error:
            return reject(channel, method, name, f"missing field {error}")
        except (ValueError, TypeError) as error:
            return reject(channel, method, name, error)
        for payload in outgoing or []:
            properties_out = pika.BasicProperties(
                delivery_mode=2, content_type="application/json", message_id=properties.message_id,
            )
            channel.basic_publish(EXCHANGE, emits, json.dumps(payload), properties_out)
        channel.basic_ack(method.delivery_tag)
        logging.info("%s: done", name)

    logging.info("listening on %s", queue)
    channel.basic_consume(queue, on_message)
    channel.start_consuming()
