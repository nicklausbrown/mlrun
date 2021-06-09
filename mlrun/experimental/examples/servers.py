import mlrun.experimental as ml


class CustomServer(ml.ModelServerBase):

    def load(self, model, context):
        self.model = self.load_model(model)

    def predict(self, event):
        self.model.predict(event)
