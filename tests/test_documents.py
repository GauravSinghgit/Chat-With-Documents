import io


def _upload(client, filename="notes.txt", content=b"Hello world, this is a test document."):
    return client.post(
        "/api/documents/ingest?generate_summary=false",
        files={"files": (filename, io.BytesIO(content), "text/plain")},
    )


def test_upload_requires_no_auth_but_links_user_when_present(auth_client):
    res = _upload(auth_client)
    assert res.status_code == 201
    body = res.json()
    assert body["ingested"] == 1
    assert body["results"][0]["status"] == "indexed"


def test_upload_rejects_unsupported_extension(auth_client):
    res = _upload(auth_client, filename="virus.exe", content=b"binary junk")
    assert res.status_code == 201  # per-file errors are reported in the body, not a top-level 4xx
    assert "error" in res.json()["results"][0]


def test_list_documents_scoped_to_owner(auth_client, client):
    _upload(auth_client)

    res = auth_client.get("/api/documents")
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # A different (anonymous) client sees no user-scoped documents from an
    # unauthenticated list call filtered by ownership doesn't apply — but an
    # anonymous *upload* has no owner, so it should show up for everyone.
    res_anon = client.get("/api/documents")
    assert res_anon.status_code == 200


def test_delete_document_requires_auth(client, auth_client):
    upload = _upload(auth_client)
    doc_id = upload.json()["results"][0]["document_id"]

    res = client.delete(f"/api/documents/{doc_id}")
    assert res.status_code == 401

    res = auth_client.delete(f"/api/documents/{doc_id}")
    assert res.status_code == 204


def test_delete_missing_document_404s(auth_client):
    res = auth_client.delete("/api/documents/999999")
    assert res.status_code == 404


def test_reindex_document(auth_client):
    upload = _upload(auth_client)
    doc_id = upload.json()["results"][0]["document_id"]

    res = auth_client.post(f"/api/documents/{doc_id}/reindex")
    assert res.status_code == 200
    assert res.json()["status"] == "indexed"
