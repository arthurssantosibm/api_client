def test_internal_headers_fixture(internal_headers):
    assert internal_headers["X-Internal-Key"] == "INTERNAL_SECRET"
