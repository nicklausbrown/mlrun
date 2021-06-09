# Introduction
Ideas for the mlrun api. 

1. I have limited documentation in the code to emphasize the readability/learnability of the classes and methods.

1. importing mlrun as ml solves a number of problems. The convenience function code_to_function and many other classes have too many parameters IMO. Importing ml allows us to have an "import *" syntax which is namespaced to ml. The public API can be defined within that namespace. Anything available in ml.<class or function> would be public. Furthermore, this promotes composition of classes with ease - avoiding long imports `from mlrun.blah.foo.this import Class`. Convenience functions can still wrap this, but they should be indicated as convenience entrypoints into the main API.

1. There is a split in functionality between the idea of a Run and a Server with mlrun. A run is batch oriented, thus has a beginning and end. A server has no beginning or end, it exists to respond to certain input in a timely manner. Both runs and servers should be monitored. 
   
1. Runs and servers should receive a runtime engine to determine their execution. Runtimes contain their own specs and code injection. Nuclio is the default runtime for serving, but it could conceivably be extended to Dask and Spark if desired.
   
1. Configuration should be designed as configurable from the start. Nothing should happen with the config from simply importing mlrun, as this slows down imports for all development even when irrelevant. Config should be easily collectable from the environment, but there are many other use cases.
   
1. The API should attempt to unify the interfaces. We should standardize on words like "add" or "with" and use them everywhere. When possible, we should adopt the same vocabulary for runs and servers in the orchestration phase - like .local() or .execute(). 

1. Both Runs and Servers should have some way to nest their execution. In the examples below, the GraphServer can accept a DAG with servers and a Pipeline can accept a DAG of Runs (and server setups). 

## Simple Example
```python
import mlrun.experimental as ml

ml.Config()\
    .from_environment()\
    .parity(local='Users/me/project/location',
            remote='Remote/path/with/same/intent')
    


preprocessor = ml.Run(name='preprocessing',
                      engine=ml.DaskRuntime(),
                      datastores=ml.DataStore())
preprocessor.local()
results = preprocessor.execute()
results.summary()


training = ml.TrainingRun(name='tensorflow-training',
                          engine=ml.HorovodRuntime(),
                          datastores=ml.DataStore())
training.local()
results = training.execute()
model = results.model


function = ml.NuclioFunction(inject_config=True)
function.add(ml.DataStore())
function.add(ml.Secret('s3-read-access'))

server = ml.TensorflowServer(engine=function,
                             models=model,
                             inputs=ml.FeatureStore('online-feature-set').vector())

server.local()
response = server.execute(ml.FeatureVector([0, 1, 2, 3]))
server.deploy()
response = server.execute()

mlops_pipeline = ml.Pipeline(steps=[preprocessor, training, server])
mlops_pipeline.local()
mlops_pipeline.execute()

mlops_pipeline.kfp  # access to the underlying kfp for direct implementation
mlops_pipeline.add_trigger(server.monitoring,  # trigger execution if the model server monitor sets off an alarm
                           require_approval=True)  # adds a notification and approval hook
mlops_pipeline.add_trigger(schedule='24h')  # always retrain at least once a day
mlops_pipeline.register(transfer_local=True)  # attach the pipeline to an mlrun server, add local results / artifacts to remote db
mlops_pipeline.execute()  # start a remote run of the pipeline

```

## Local flag

This is useful for development and especially for safe testing.

```python
import mlrun.experimental as ml

ml.Config()\
    .from_environment()\
    .default_local()  # remove all calls to .local() and use by default

```

## Composed Servers

Servers should be able to be run together alongside regular steps in graphs. There should be no difference between local and remote syntax other than .local(). If it doesn't work remotely, it should work locally and vice-versa.

```python

import mlrun.experimental as ml
from mlrun.experimental.examples.servers import CustomServer


ml.Config()\
    .private_hub('<some way to connect to private function hub>')

# having the graph be a totally separate nuclio function could
# be useful to provide a manager pattern (give info about the full 
# graph at runtime) allow this to be optional, but it could be great
# for monitoring.
graph = ml.GraphServer(engine=ml.NuclioFunction(),  
                       mode='async',                
                       tag='pipeline-1234') 

class Preprocessor:
    
    def __init__(self, param1):
        self.param1 = param1
        
    def do(self, event: ml.VectorEvent):
        for index, val in enumerate(event.vector):
            event.vector[index] = val / self.param1
        return event

        
gpu = ml.NuclioFunction().add_limits(gpu=1)
tf_gpu = gpu.copy().commands(['pip install tensorflow'])
        
# Graphs should accept initialized objects for autocomplete, also imports should "just work"
graph.step(Preprocessor(param1=2))\
     .step(ml.TensforflowServer(registry="hub://private/tensorflow-model-server", engine=tf_gpu), name='tf_model')\
     .step(ml.Server(CustomServer(ml.Model('onnx-model')), engine=gpu.copy()), name='custom_model')\
     .stream(producers=['tf_model', 'custom_model'])  # stream name should be derived by default, allow a name parameter

graph.local()
graph.execute(ml.FeatureVector([0, 1, 2, 3]))
graph.deploy()

```