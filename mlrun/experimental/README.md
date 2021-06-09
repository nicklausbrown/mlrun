# Introduction
Ideas for the mlrun api

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
response = server.invoke(ml.FeatureVector([0, 1, 2, 3]))
server.deploy()
response = server.invoke()

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
        
    def do(self, event):
        for index, val in enumerate(event.vector):
            event.vector[index] = val / self.param1
        return event

        
gpu = ml.NuclioFunction().with_limits(gpu=1)
tf_gpu = gpu.copy().commands(['pip install tensorflow'])
        
# Graphs should accept initialized objects for autocomplete, also imports should "just work"
graph.step(Preprocessor(param1=2))\
     .step(ml.TensforflowServer(registry="hub://private/tensorflow-model-server", engine=tf_gpu), name='tf_model')\
     .step(ml.Server(CustomServer(ml.Model('onnx-model')), engine=gpu.copy()), name='custom_model')\
     .stream(producers=['tf_model', 'custom_model'])  # stream name should be derived by default, allow a name parameter

graph.local()
graph.invoke(ml.FeatureVector([0, 1, 2, 3]))
graph.deploy()

```