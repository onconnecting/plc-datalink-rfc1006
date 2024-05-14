import requests
import logging

# Logger instance defined in `init.py`
logger = logging.getLogger('application_logger')


class CouchDBService:
    def __init__(self, base_url, username, password,database_name):
        self.base_url = base_url
        self.auth = (username, password)
        self.database_name=database_name

    def get_all_docs(self):
        url = f"{self.base_url}/{self.database_name}/_all_docs?include_docs=true"
        return self._make_request("GET", url)

    def get_doc(self, doc_id):
        url = f"{self.base_url}/{self.database_name}/{doc_id}"
        return self._make_request("GET", url)

    def create_doc(self, data):
        """ Create or update a document using PUT with an explicit _id derived from machineName. """
        machine_name = data['machineData']['machineName']
        # Set the _id field in the data dictionary to the machineName
        data['_id'] = machine_name
        # Construct the URL to include the _id for a PUT request
        url = f"{self.base_url}/{self.database_name}/{machine_name}"
        return self._make_request("PUT", url, json=data)

    def update_doc(self, doc_id, data):
        # Must include '_rev' in data for update to work
        url = f"{self.base_url}/{self.database_name}/{doc_id}"
        return self._make_request("PUT", url, json=data)

    def delete_doc(self, doc_id, rev):
        url = f"{self.base_url}/{self.database_name}/{doc_id}?rev={rev}"
        return self._make_request("DELETE", url)

    def _make_request(self, method, url, **kwargs):
        try:
            # Include authentication in every request
            response = requests.request(method, url, auth=self.auth, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
