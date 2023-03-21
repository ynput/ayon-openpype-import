import requests
from typing import Any
from .common import config


class GraphQLResponse:
    def __init__(self, **response):
        self.data = response.get("data", {})
        self.errors = response.get("errors", {})

    def __len__(self):
        return not bool(self.errors)

    def __repr__(self):
        if self.errors:
            msg = f"errors=\"{self.errors[0]['message']}\""
        else:
            msg = 'status="OK">'
        return f"<GraphQLResponse {msg}>"

    def __getitem__(self, key):
        return self.data[key]


class Ayon:
    def __init__(self):
        self.server_url = config.server_url.rstrip("/")
        self.access_token = config.api_key
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
                "X-Api-Key": config.api_key,
            }
        )

    def gql(self, query, **kwargs):
        data = {"query": query, "variables": kwargs}
        response = self.session.post(self.server_url + "/graphql", json=data)
        return GraphQLResponse(**response.json())

    def request(self, method, endpoint, **kwargs):
        response = self.session.request(
            method, self.server_url + "/api/" + endpoint, **kwargs
        )
        if response.status_code in [204, 201]:
            return None
        if not response:
            raise Exception("Error during request", response)
        return response.json()

    def __getattr__(self, method: str):
        def wrapper(endpoint: str, **kwargs: dict[str, Any]):
            return self.request(method, endpoint, **kwargs)

        return wrapper

    def download_private_file(self, source_path: str, target_path: str):
        url = f"{self.server_url}/addons/{config.addon_name}/{config.addon_version}"
        url += f"/private/{source_path}"
        res = requests.get(url, stream=True, headers={"X-Api-Key": self.access_token})
        res.raise_for_status()
        with open(target_path, "wb") as f:
            f.write(res.content)

    def update_event(self, event_id: str, **kwargs: dict[str, Any]):
        return self.patch(f"events/{event_id}", json=kwargs) 


ayon = Ayon()
