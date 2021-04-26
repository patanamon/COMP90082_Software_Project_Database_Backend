from django.test import Client, TestCase
from TeamSPBackend.common.choices import RespCode


class JiraTestCases(TestCase):

    def setUp(self):
        session = self.client.session
        session["user"] = {
            "atl_username": "",
            "atl_password": ""
        }   
        session.save()

    def test_get_individual_issue_success(self):
        """
        Tests the issue per student query success
        """
        team = "swen90013-2020-sp"
        student = "xinbos"
        response = self.client.get('/api/v11/jira/' + team + '/tickets/' + student)
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_team_issue_success(self):
        """
        Tests the issue per student query success
        """
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/tickets')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_individual_comment_count_success(self):
        """
        Tests the issue per student query success
        """
        team = "swen90013-2020-sp"
        student = "xinbos"
        response = self.client.get('/api/v11/jira/' + team + '/comments/' + student)
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_sprint_dates_success(self):
        """
        Tests the issue per student query success
        """
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/sprint_dates')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")