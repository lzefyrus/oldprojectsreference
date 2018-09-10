from locust import HttpLocust, TaskSet, task
import random
import json

AUTH = 'a8f693e5cd614b8f998170514ab10b8c'
DIF = {'easy': 4, 'medium': 5, 'hard': 6, 'impossible': 7}


class WebsiteTasks(TaskSet):
    # def on_start(self):
    #     self.client.post("/login", {
    #         "username": "test_user",
    #         "password": ""
    #     })


    @task(3)
    def index(self):
        self.client.get("/api/challenge", headers={"Authorization": AUTH})

    @task(3)
    def user(self):
        user = self.client.get("/api/user", headers={"Authorization": AUTH})

    @task(14)
    def game(self):
        level = random.choice(['easy', 'medium', 'hard', 'impossible'])
        game = self.client.get("/api/game/{}".format(level), headers={"Authorization": AUTH})
        tips = self.client.get("/api/tips/{}".format(level), headers={"Authorization": AUTH})
        resp = json.loads(game.content.decode())
        icons = [i.get('code') for i in resp.get('icons')]
        tt = random.sample(icons, DIF.get(level))
        payload = {'sequence': '|'.join(tt)}
        self.client.post("/api/game/{}".format(level), data=json.dumps(payload),  headers={"Authorization": AUTH, 'content-type': 'application/json'})
        if random.randint(0, 50) in [1,5,35]:
            self.client.get("/api/user", headers={"Authorization": AUTH})



class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    host = 'http://test-api.next.me'
    min_wait = 5000
    max_wait = 15000
