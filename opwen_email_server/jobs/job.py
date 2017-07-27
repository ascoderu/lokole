from typing import Type

from opwen_email_server.services.queue_consumer import QueueConsumer


def main(queue_consumer_factory: Type[QueueConsumer]):
    consumer = queue_consumer_factory()
    consumer.run_forever()
