# Introduction
Ideas for the mlrun api. 

1. I have limited documentation in the code to emphasize the readability/learnability of the classes and methods. In general, I have prioritized polymorphism and "composition over inheritance" with my thoughts in this design. Servers and Runs may be subclassed, but runtimes are composed of things like specs and code and added into Servers and Runs - because they're distinctly different entities. Above all - [things not strings](https://blog.google/products/search/introducing-knowledge-graph-things-not/).

1. importing mlrun as ml solves a number of problems. The convenience function code_to_function and many other classes have too many parameters IMO. Importing ml allows us to have an "import *" syntax which is namespaced to ml. The public API can be defined within that namespace. Anything available in ml.<class or function> would be public. Furthermore, this promotes composition of classes with ease - avoiding long imports `from mlrun.blah.foo.this import Class`. Convenience functions can still wrap this, but they should be indicated as convenience entrypoints into the main API.

1. There is a split in functionality between the idea of a Run and a Server with mlrun. A run is batch oriented, thus has a beginning and end. A server has no beginning or end, it exists to respond to certain input in a timely manner. Servers also abstract code and configuration to simplify developer experience when deploying data and machine learning components. Both runs and servers should be monitored. 
   
1. Runs and servers should receive a runtime engine to determine their execution. Runtimes contain their own specs and code injection. Nuclio is the default runtime for serving, but it could conceivably be extended to Dask and Spark if desired.
   
1. Configuration should be designed as configurable from the start. Nothing should happen with the config from simply importing mlrun, as this slows down imports for all development even when irrelevant. Config should be easily collectable from the environment, but there are many other use cases.
   
1. The API should attempt to unify the interfaces. We should standardize on words like "add" or "with" and use them everywhere. When possible, we should adopt the same vocabulary for runs and servers in the orchestration phase - like .local() or .execute(). 

1. Both Runs and Servers should have some way to nest their execution. In the examples below, the GraphServer can accept a DAG with servers and a Pipeline can accept a DAG of Runs (and server setups). 

## Simple Example
```python
import mlrun.experimental as ml

ml.Config()\
    .from_environment()\
    .parity(path={'local': 'Users/me/project/location',  # used to maintain a local / remote mapping with path as an option
                  'remote': 'Remote/path/with/same/intent'})
    


preprocessor = ml.Run(name='preprocessing',
                      engine=ml.DaskRuntime(),
                      datastores=ml.DataStore())  # map a volume of some sort into the Run, use parity
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
                             inputs=ml.FeatureStore('online-feature-set').vector(),  # automatically register trigger with this
                             monitors=[ml.FeatureDrift(statistics=True),  # use the model training statistics to measure drift
                                       ml.ConceptDrift()])
server.local()
response = server.execute(ml.FeatureVector([0, 1, 2, 3]))
server.deploy()
response = server.execute()  # use the feature store definition to automatically call on most recent record

mlops_pipeline = ml.Pipeline(steps=[preprocessor, training, server]) # chained linear steps, don't assign to use below 
mlops_pipeline.custom('<kubeflow pipeline definition>')  # access to the underlying kfp for direct implementation

mlops_pipeline.local()
mlops_pipeline.execute()

mlops_pipeline.add_trigger(server.monitoring,  # trigger execution if the model server monitor sets off an alarm
                           require_approval=True)  # adds a notification and approval hook
mlops_pipeline.add_trigger(schedule='24h')  # always retrain at least once a day
mlops_pipeline.deploy(transfer_local=True, register_only=True)  # attach the pipeline to an mlrun server, add local results / artifacts to remote db, only build and register (don't run)
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
                       async_mode=True,                
                       tag='pipeline-1234') 

class Preprocessor:
    
    def __init__(self, param1):
        self.param1 = param1
        
    def do(self, event: ml.VectorEvent):
        for index, feature in enumerate(event.vector):
            event.vector[index] = feature / self.param1
        return event

        
gpu = ml.NuclioFunction().add_limits(gpu=1)
tf_gpu = gpu.copy().commands(['pip install tensorflow>=2.4.0'])  # allow overriding the registry config
        
# Graphs should accept initialized objects for autocomplete, also imports should "just work"
graph.step(Preprocessor(param1=2))\
     .step(ml.TensforflowServer(registry="hub://private/tensorflow-model-server", engine=tf_gpu), group='fan')\
     .step(ml.Server(CustomServer(ml.Model('onnx-model')), engine=gpu.copy()), group='fan')\
     .stream(inputs='fan')  # stream name should be derived by default, allow a name parameter
   # .fan_in(inputs='fan', stream=ml.V3ioStream())  # alternatively, define a method that automatically generates the stream
   #  maybe include merge=StreamMerger(key=<some partition key>) to join streams in fan_in method      
   # .fan_out(outputs='fan', stream=ml.KafkaTopic())  # another possible option which could emit messages out to multiple consumers

graph.local()
graph.execute(ml.FeatureVector([0, 1, 2, 3]))

graph.deploy()
# allow executing and reading the graph stream output remotely, for the most recent 10 messages
with graph.listen():
    graph.execute(ml.FeatureStore('online-feature-set').tail(10).vector())

```