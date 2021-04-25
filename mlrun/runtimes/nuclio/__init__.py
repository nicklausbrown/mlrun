import yaml
import json
from pydantic import BaseModel


def to_camel(string: str) -> str:
    words = string.split('_')
    return words[0] + ''.join(word.capitalize() for word in words[1:])


class CamelBaseModel(BaseModel):
    class Config:
        extra = 'forbid'
        alias_generator = to_camel
        use_enum_values = True

    def to_dict(self, *args, **kwargs):
        return self.dict(*args, **kwargs)

    def to_yaml(self):
        # take advantage of cool things Pydantic does like obfuscate secrets
        return yaml.dump(json.loads(self.to_json()))

    def to_json(self):
        return self.json(by_alias=True, exclude_none=True)
