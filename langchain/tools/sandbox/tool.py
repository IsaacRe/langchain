# Credit to cangcang-zcr@github - https://github.com/hwchase17/langchain/issues/2301
from langchain.tools.base import BaseTool
import requests
import os


class SandboxTool(BaseTool):
    """Tool to run shell commands in isolated container."""

    name: str = "terminal"
    """Name of tool."""

    description: str = f"Run shell commands on this Linux machine. To exit the current shell, output '^D'."
    """Description of tool."""

    def _run(self, query: str) -> str:
        return self.remote_request(query)

    async def _arun(self, tool_input: str) -> str:
        raise NotImplementedError("SandboxTool does not support async")

    def remote_request(self, query: str) -> str:
        url = os.getenv("SANDBOX_ENDPOINT_URL", "http://localhost:8000/execute")
        headers = {
            "Content-Type": "application/json",  
        }
        exit_ = query.strip("'\"").strip() == "^D"
        json_data = {
            "exit": exit_,
            "code": query
        }
        response = requests.post(url, headers=headers, json=json_data)

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            return f"Request failed, status code: {response.status_code}"
