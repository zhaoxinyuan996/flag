"""
压测
"""
from locust import HttpUser, TaskSet, task


# 定义用户行为
class UserBehavior(TaskSet):

    @task
    def bky_index(self):
        self.client.get("/api/test/user-info", json={},headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwMzY2MTYzMSwianRpIjoiZDk4YjAwMzItNWJkOC00MmFiLThkNDMtMjRlOWFmMzU3MjQ1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjVjMWYyYTY0LWM2MjktNDllMi04YTJiLTk3MmZkYTUwNzVhNyIsIm5iZiI6MTcwMzY2MTYzMSwiZXhwIjoxNzA5NjYxNTcxfQ.YSh6PpjY-adcPtcrrMStxCW_jVfpfaCcYb8_ReB9GsU'})

    # @task(2)
    # def blogs(self):
    #     self.c
    #     self.client.post("/user/user-info")


class WebsiteUser(HttpUser):
    host = "https://www.flag-app.asia"
    tasks = [UserBehavior]
    min_wait = 1500
    max_wait = 5000


if __name__ == '__main__':
    import os
    cmd = ' locust -f street.py'
    os.system(cmd)
