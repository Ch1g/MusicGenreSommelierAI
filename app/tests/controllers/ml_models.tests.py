from fastapi.testclient import TestClient
from sqlmodel import Session

from music_genre_sommelier.models.ml_model import MLModel

def test_list_models_200(client: TestClient, test_session: Session):
    test_session.add(MLModel(model_path="/models/a.pt", prediction_cost=1.0))
    test_session.add(MLModel(model_path="/models/b.pt", prediction_cost=2.0))
    test_session.commit()

    resp = client.get("/api/ml-models/")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
