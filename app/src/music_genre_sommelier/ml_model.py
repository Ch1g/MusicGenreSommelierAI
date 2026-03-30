class MLModel:
    def __init__(self, id: int, model_path: str, prediction_cost: float):
        self.id = id
        self.model_path = model_path
        self.prediction_cost = prediction_cost

    # TODO: Реализовать позже
    def predict(self, spectrogram_path: str):
        return