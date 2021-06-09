# Introduction
An idea for the mlrun api

## Simple Example
```python
import mlrun.experimental as ml

ml.Config()\
    .from_environment()\
    .parity(lacal='Users/me/project/location',
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

```python

import mlrun.experimental as ml
from mlrun.experimental.examples.servers import CustomServer


ml.Config()\
    .private_hub('<some way to connect to private function hub>')

graph = ml.GraphServer(engine=ml.NuclioFunction(),  # having the graph be a totally separate nuclio function could
                       mode='async')                # be useful to provide a manager pattern (give info about the full graph at runtime)
                                                    # allow this to be optional, but it would be great for monitoring
class Preprocessor:
    
    def __init__(self, param1):
        self.param1 = param1

        
# Graphs should accept initialized objects for autocomplete, also imports should "just work"
graph.step(Preprocessor(param1='this_parameter'))\
     .step(ml.TensforflowServer(registry="hub://private/tensorflow-model-server"), name='tf_model')\
     .step(ml.Server(CustomServer(ml.Model('onnx-model'))), name='custom_model')\
     .stream(producers=['tf_model', 'custom_model'])

graph.local()
graph.invoke(ml.FeatureVector([0, 1, 2, 3]))
graph.deploy()

```