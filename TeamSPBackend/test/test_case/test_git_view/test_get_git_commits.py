from django.test import TestCase
from TeamSPBackend.git.models import StudentCommitCounts, GitCommitCounts
from TeamSPBackend.test.utils import object_creation_helpers, login_helpers

class GetGitCommitsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        object_creation_helpers.createGenericAdmin()
   
    def setUp(self):
        # login first
        login_helpers.login(self.client)

    def test_get_individual_commits(self):
        """
        Test the function for the API: POST /api/v1/git/commit
        Search for individual contribution
        """

        url = "/api/v1/git/individual_commits"
        # data = {
        #     #"url": "https://github.com/LikwunCheung/TeamSPBackend",
        #     #"author": "Procyon1996"
        # }
        #
        # response = self.client.post(url, data=data, content_type="application/json")
        # all_entries =StudentCommitCounts.objects.all()
        # for item in all_entries:
        #     print(str(item.student_name)+" : "+str(item.commit_counts))
        # for commit in response.json()["data"]['commits']:
        #     if commit['author'] != 'Procyon1996':
        #         tag_1 = 1
        #     if commit['author'] == 'Procyon1996':
        #         tag_2 = 0
        # self.assertEqual(tag_1 & tag_2, 0)

    def test_git_date(self):
        url = "/api/v1/git/commit"
        data = {
            "url": "https://github.com/LikwunCheung/TeamSPBackend",
            "after": 1501141532000,
            "before": 1611141532000
        }
        response = self.client.post(url, data=data, content_type="application/json")

        flag = True
        for commit in response.json()["data"]['commits']:
            if commit['date'] < 1501141532000:
                flag = False
            elif commit['date'] > 1611141532000:
                flag = False
        self.assertEqual(flag, True)
        # print("test_git_date:")
        dic = dict(
            total=response.json()["data"]['total'],
            relation_id=response.json()["data"]['relation_id'],
            date=response.json()["data"]['date'],
            url=response.json()["data"]['space_key']
        )
        print(dic)

    def test_get_total_commits(self):
        """
                Test the function for the API: POST /api/v1/git/commit
                Search for total contribution
                """
        url = "/api/v1/git/commit"
        data = {
            "url": "https://github.com/LikwunCheung/TeamSPBackend",
            # "author": "Procyon"
        }
        # get_git_commits(data=data)
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertNotEqual(response.json()["data"], None)
        # self.assertEqual(response.status_code, 200, "response code is not 200")
        # print(response.json())

        # d = get_git_commits(request = data)
        # self.assertEqual(d.status_code, 200)

    def test_git_pr(self):
        url = "/api/v1/git/pullrequest"
        data = {
            "url": "https://github.com/LikwunCheung/TeamSPBackend"
        }
        response = self.client.post(url, data=data, content_type="application/json")
        # print("pull request json file:")
        # print(response.json())


if __name__ == '__main__':
    TestCase.main()
