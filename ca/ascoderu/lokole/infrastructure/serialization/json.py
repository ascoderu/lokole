import json

from ca.ascoderu.lokole.infrastructure.serialization.interfaces import Serializer


class JsonSerializer(Serializer):
    _encoding = 'utf-8'
    _separators = (',', ':')

    def serialize(self, obj):
        serialized = json.dumps(obj, separators=self._separators)
        return serialized.encode(self._encoding)

    def deserialize(self, serialized):
        decoded = serialized.decode(self._encoding)
        return json.loads(decoded)
