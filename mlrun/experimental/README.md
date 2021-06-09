# Introduction
An idea for the mlrun api

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
model = training.model

function = ml.NuclioFunction(inject_config=True)
function.add(ml.DataStore())

server = ml.TensorflowServer(engine=function,
                             models=model,
                             inputs=ml.FeatureStore('online-feature-set').vector())

server.local()
response = server.invoke(ml.FeatureVector([0, 1, 2, 3]))
server.deploy()
response = server.invoke()

mlops_pipeline = ml.Pipeline(steps=[preprocessor, training, server])
mlops_pipeline.kfp  # access to the underlying kfp for direct implementation
mlops_pipeline.register()
mlops_pipeline.execute()

```