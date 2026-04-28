from sqlmodel import Session

from music_genre_sommelier.models.ml_model import MLModel


def test_create_ml_model(test_session: Session):
    model = MLModel(model_path="/models/resnet50.pt", prediction_cost=1.5)
    test_session.add(model)
    test_session.commit()
    test_session.refresh(model)

    assert model.id is not None
    assert model.model_path == "/models/resnet50.pt"
    assert model.prediction_cost == 1.5
    assert model.input_width == 224
    assert model.input_height == 224
