from django.test import TestCase, Client
from TeamSPBackend.common.choices import RespCode


# Create your tests here.
class GeneralTestImportProjectInBatch(TestCase):
    def test_import_projects_in_batch(self):
        data = {
            "coordinator": "bob",
            "project_list": "aa,bb,cc"
        }
        response = self.client.post('/api/v1/project/import', data=data, content_type="application/json")
        self.assertEqual(response.json()["code"], -1, "response code is not -1")