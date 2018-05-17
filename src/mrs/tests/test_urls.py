def test_manifest(client):
    r = client.get('/manifest.json')
    assert r.status_code == 200
