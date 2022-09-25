import unittest

from website import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.access_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNjUzMjM3MTY0LCJqdGkiOiJlMzVmNWRkZC1mMmMxLTQ3NWMtODJjZS0xZDZmMTM4YjIxODYiLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjoxLCJuYmYiOjE2NTMyMzcxNjQsImV4cCI6MTY1MzIzODA2NH0.mVJn4KevTuL2lqnVX6ZTTcpWJ8LU-md7Pb8yaOKY-Mc"

    def test_echo(self):
        response = self.client.get("/echo")
        expected_response = {"status" : 200, "msg" : "OK"}
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.get_json(), expected_response)

    def test_add_language(self):
        #access_token = create_access_token('testuser')
        headers = {
            'Authorization': 'JWT {}'.format(self.access_token)
        }
        response = self.client.post("/languages", json={"language_name" : "Arabic", "language_code" : "arb"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["msg"], "Language added")
        self.assertEqual(response.get_json()["status"], 201)

