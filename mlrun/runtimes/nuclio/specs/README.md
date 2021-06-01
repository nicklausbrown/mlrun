
# Motivation

Documentation, serialization, and auto-complete can require a lot of code, but they are imperative for a simple and less error-prone development experience. Pydantic provides much of this for free, and it is one of the [reasons that FastAPI](https://fastapi.tiangolo.com/features/#pydantic-features) has been so successful. 

As such, the base of mlrun and nuclio - which are serialized into yaml/json - would benefit from using Pydantic. It will increase readability and auto-complete in modern IDEs like pycharm. It will also directly serialize classes and any nested classes predictably. Implementing additional functionality on top of these classes will be more consistent due to autocomplete and linting of types.

# Example

Check out the docstrings for more details! Also, I highly recommend trying out autocomplete in pycharm after [installing the plugin](https://pydantic-docs.helpmanual.io/pycharm_plugin/)

```python
from mlrun.runtimes.nuclio.specs import *  # don't do this outside this example :)

config = NuclioConfig()

volume = VolumeSpec(volume=V3ioVolume())
volume.name('v3io')\
      .map('/inside_function', '/users/v3io_user/path')\
      .add_secret('StringYouWillNotSee')

config.add_volume(volume)

trigger = V3ioStreamTrigger()
trigger.attributes.consumer_group = 'nuclio'
trigger.attributes.container_name = 'users'
trigger.attributes.stream_path = 'v3io_user/stream-path'
trigger.add_secret('StringYouWillNotSee')
# # optionally change trigger name, comes with 'v3io'
# trigger.name('special-v3io')

# # or even more convenient
# trigger = create_v3io_trigger(path='v3io_user/stream-path',
#                               container='users',
#                               access_key='StringYouWillNotSee', # also getenv V3IO_ACCESS_KEY
#                               max_workers=10) 
# trigger.attributes.consumer_group = 'nuclio'


# # or for a different streaming option
# trigger = create_kafka_trigger(topic='important-topic',
#                                brokers=['broker1', 'broker2'],
#                                max_workers=10) 

config.add_trigger(trigger)

print(config.to_yaml())
```
