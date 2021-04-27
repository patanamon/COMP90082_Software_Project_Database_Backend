from django.test import Client, TestCase
from TeamSPBackend.common.choices import RespCode

# bridging solution for non-secure tls
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class JiraTestCases(TestCase):

    def setUp(self):
        session = self.client.session
        session["user"] = {
            "atl_username": "",
            "atl_password": ""
        }   
        session.save()

    def test_get_individual_issue_success(self):
        team = "swen90013-2020-sp"
        student = "xinbos"
        response = self.client.get('/api/v11/jira/' + team + '/tickets/' + student)
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_team_issue_success(self):
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/tickets')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_individual_comment_count_success(self):
        team = "swen90013-2020-sp"
        student = "xinbos"
        response = self.client.get('/api/v11/jira/' + team + '/comments/' + student)
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_sprint_dates_success(self):
        """
        Tests the issue per student query success
        """
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/issues_per_sprint')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_issues_per_sprint_success(self):
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/sprint_dates')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_ticket_count_team_timestamped_success(self):
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/ticket_count')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    def test_get_contributions_success(self):
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/contributions')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")

    """
    # not applicable yet
    def test_get_jira_cfd_success(self):
        
        team = "swen90013-2020-sp"
        response = self.client.get('/api/v11/jira/' + team + '/jira_cfd')
        self.assertEqual(response.json()["code"], RespCode.success.value.key, "response is not success")
    """