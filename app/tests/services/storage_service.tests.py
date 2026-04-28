import io

from music_genre_sommelier.services.storage_service import StorageDirectory, StorageService


def test_store_bytes_writes_file(tmp_path):
    svc = StorageService(base_path=tmp_path)
    path = svc.store(b"hello", StorageDirectory.AUDIOS, "test.wav")
    assert path.read_bytes() == b"hello"


def test_store_file_like_writes_file(tmp_path):
    svc = StorageService(base_path=tmp_path)
    buf = io.BytesIO(b"data")
    path = svc.store(buf, StorageDirectory.SPECTROGRAMS, "spec.png")
    assert path.read_bytes() == b"data"


def test_delete_removes_file(tmp_path):
    svc = StorageService(base_path=tmp_path)
    path = svc.store(b"x", StorageDirectory.AUDIOS, "del.wav")
    assert path.exists()
    svc.delete(path)
    assert not path.exists()


def test_delete_missing_file_is_noop(tmp_path):
    svc = StorageService(base_path=tmp_path)
    svc.delete(tmp_path / "nonexistent.wav")  # must not raise
