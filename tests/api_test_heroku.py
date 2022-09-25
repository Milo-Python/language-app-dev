import unittest
import requests
import json

url = "https://language-app-dev.herokuapp.com"


def get_token():
    payload = json.dumps({
        "email": "nowy",
        "password": "1234"
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url + "/login", headers=headers, data=payload)
    return response.json()["access_token"]


class TestCases(unittest.TestCase):
    def setUp(self):
        self.token = get_token()

    def test_get_all_words(self):
        token = get_token()
        headers = {
            "Authorization" : "Bearer " + self.token
        }
        response = requests.request("GET", url + "/words", headers=headers)
        print(response.text)
        self.assertTrue(len(response.json()) > 0)

    def test_add_word(self):
        payload = json.dumps({
            "word_name": "browser",
            "context": "Use to see websites",
            "language_name" : "English"
        })

        token = get_token()
        headers = {
            "Authorization": "Bearer " + self.token,
            'Content-Type': 'application/json'
        }
        response = requests.request("POST", url + "/words", headers=headers, data=payload)
        print(response.text)
        print(response.status_code)
