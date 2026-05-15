import pytest
from requests.exceptions import HTTPError

from src.services.couchdb_service import CouchDBService


@pytest.fixture
def service():
    return CouchDBService('http://couchdb-test:5984', 'admin', 'secret', 'datalink')


def test_get_all_docs_calls_all_docs_endpoint(service, requests_mock):
    payload = {'rows': [{'id': 'm1', 'doc': {}}]}
    requests_mock.get(
        'http://couchdb-test:5984/datalink/_all_docs',
        json=payload,
    )
    assert service.get_all_docs() == payload
    assert requests_mock.last_request.qs == {'include_docs': ['true']}


def test_get_doc_returns_document(service, requests_mock):
    payload = {'_id': 'm1', '_rev': '1-abc', 'machineData': {'machineName': 'm1'}}
    requests_mock.get('http://couchdb-test:5984/datalink/m1', json=payload)
    assert service.get_doc('m1') == payload


def test_get_doc_404_raises_httperror(service, requests_mock):
    requests_mock.get(
        'http://couchdb-test:5984/datalink/missing',
        status_code=404,
        json={'error': 'not_found'},
    )
    with pytest.raises(HTTPError) as excinfo:
        service.get_doc('missing')
    assert excinfo.value.response.status_code == 404


def test_create_doc_sets_id_and_puts(service, sample_config_dict, requests_mock):
    requests_mock.put(
        'http://couchdb-test:5984/datalink/sample',
        json={'ok': True, 'id': 'sample', 'rev': '1-aaa'},
    )
    result = service.create_doc(sample_config_dict)
    assert result == {'ok': True, 'id': 'sample', 'rev': '1-aaa'}
    sent = requests_mock.last_request.json()
    assert sent['_id'] == 'sample'
    assert sent['machineData']['machineName'] == 'sample'


def test_create_doc_409_conflict_raises(service, sample_config_dict, requests_mock):
    requests_mock.put(
        'http://couchdb-test:5984/datalink/sample',
        status_code=409,
        json={'error': 'conflict'},
    )
    with pytest.raises(HTTPError) as excinfo:
        service.create_doc(sample_config_dict)
    assert excinfo.value.response.status_code == 409


def test_update_doc_sends_rev(service, requests_mock):
    requests_mock.put(
        'http://couchdb-test:5984/datalink/m1',
        json={'ok': True, 'id': 'm1', 'rev': '2-bbb'},
    )
    result = service.update_doc('m1', {'_rev': '1-aaa', 'machineData': {'machineName': 'm1'}})
    assert result['rev'] == '2-bbb'
    assert requests_mock.last_request.json()['_rev'] == '1-aaa'


def test_delete_doc_passes_rev_query(service, requests_mock):
    requests_mock.delete(
        'http://couchdb-test:5984/datalink/m1',
        json={'ok': True, 'id': 'm1', 'rev': '3-ccc'},
    )
    result = service.delete_doc('m1', '2-bbb')
    assert result['rev'] == '3-ccc'
    assert requests_mock.last_request.qs == {'rev': ['2-bbb']}
