from os import getenv
from random import choice
from string import ascii_letters
from unittest import TestCase
from unittest import skipUnless
import ast
import inspect

from cached_property import cached_property
from kombu import Connection
from kombu import Exchange
from kombu import Queue

from opwen_email_server.config import QUEUE_BROKER
import opwen_email_server.integration.celery as celery


class TransportTests(TestCase):
	exchange_name = getenv('KOMBU_EXCHANGE', 'testexchange')
	queue_name = getenv('KOMBU_QUEUE', 'testqueue')
	routing_key = getenv('KOMBU_ROUTING_KEY', 'testkey')

	@cached_property
	def exchange(self) -> Exchange:
		return Exchange(self.exchange_name, 'direct', durable=True)

	@cached_property
	def queue(self) -> Queue:
		return Queue(self.queue_name, exchange=self.exchange, routing_key=self.routing_key)

	@skipUnless(QUEUE_BROKER, 'no celery broker configured')
	def test_send_message(self):
		random_message = ''.join(choice(ascii_letters)  # nosec
								 for _ in range(30))

		with Connection(QUEUE_BROKER) as connection:
			producer = connection.Producer()
			producer.publish(
				{'message': random_message, 'test': True},
				exchange=self.exchange,
				routing_key=self.routing_key,
				declare=[self.queue],
			)
	
	def test_celery_task_routes(self):
		# REFERENCE: https://stackoverflow.com/questions/3232024/introspection-to-get-decorator-names-on-a-method
		
		decorator_test_name = 'task'
		
		def get_decorators(cls):
			target = cls
			decorators = {}

			def visit_FunctionDef(node):
				decorators[node.name] = []

				for n in node.decorator_list:
					name = ''

					if isinstance(n, ast.Call):
						name = n.func.attr  if isinstance(n.func, ast.Attribute) else n.func.id
					else:
						name = n.attr if isinstance(n, ast.Attribute) else n.id

					decorators[node.name].append(name)

			node_iter = ast.NodeVisitor()
			node_iter.visit_FunctionDef = visit_FunctionDef
			node_iter.visit(ast.parse(inspect.getsource(target)))

			return decorators

		func_dict = get_decorators(celery)
		celery_module_name = celery.__name__

		for func_name, decorator_name_list in func_dict.items():
			if (not func_name[0:1] == '_') and (bool(decorator_name_list)):
				# Ignore a functon with a '_' private, internal prefix signature, or without any decorator
				
				if decorator_test_name in decorator_name_list:
					self.assertIsNotNone(celery.task_routes.get(celery_module_name + "." + func_name, None),
						"Function '" + func_name + "' not found in the task_routes dictionary in '" + celery_module_name + "' module")