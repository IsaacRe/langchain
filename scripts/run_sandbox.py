# Credit to cangcang-zcr@github - https://github.com/hwchase17/langchain/issues/2301
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict
import pexpect
from datetime import datetime, timedelta
import time
import re

READ_BUFFER = 1_000_000
CMD_PROMPT_PATH_RE = re.compile(r"^[^a-zA-Z0-9_-]*(?P<user_string>[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+):[a-zA-Z0-9_/~-]+(#|\$)\s*$")


def poll_for_output(
    process: pexpect.spawn,
    poll_time: float = 0.2,
    idle_timeout: float = 2.0,
    hard_timeout: float = 30.0,
) -> str:
    end_time = datetime.utcnow() + timedelta(seconds=hard_timeout)
    output = ""
    while True:
        remaining_time = (end_time - datetime.utcnow()).total_seconds()
        try:
            output += process.read_nonblocking(READ_BUFFER, timeout=min(remaining_time, idle_timeout)).decode()
        except pexpect.exceptions.TIMEOUT:
            return output
        except pexpect.exceptions.EOF:
            return output
        remaining_time = (end_time - datetime.utcnow()).total_seconds()
        if remaining_time <= poll_time:
            return output
        time.sleep(poll_time)


class SandboxShell:

    def __init__(self, timeout: int = 10, shell_cmd: str = "/bin/bash", user_string: str = "root@sandbox", replace_user_string: bool = True) -> None:
        self.shell_cmd = shell_cmd
        self.output_user_string = user_string
        self.replace_user_string = replace_user_string
        self.subprocess = pexpect.spawn(shell_cmd)
        cmd_prompt = self.subprocess.read_nonblocking(READ_BUFFER, timeout=0.1).decode()
        match = CMD_PROMPT_PATH_RE.search(cmd_prompt)
        self.system_user_string = ""
        if match:
            self.system_user_string = match.group("user_string")
        self.timeout = timeout

    def execute(self, command: str) -> str:
        self.subprocess.send(command + "\n")
        out = poll_for_output(self.subprocess)
        if not self.subprocess.isalive():
            self.subprocess.close()
            self.subprocess = pexpect.spawn(self.shell_cmd)
        if self.replace_user_string:
            out = out.replace(self.system_user_string, self.output_user_string)
        return out
        
    def exit(self):
        if self.subprocess is not None:
            self.subprocess.close()
            self.subprocess = None


app = FastAPI()
shell = SandboxShell()  # must run in single-worker mode


class CodeData(BaseModel):
    code: str
    exit: bool


@app.post("/execute", response_model=Dict[str, Any])
async def execute_code(code_data: CodeData):
    # if code_data.code_type == "python":
    #     try:
    #         buffer = io.StringIO()
    #         sys.stdout = buffer
    #         exec(code_data.code)
    #         sys.stdout = sys.__stdout__
    #         exec_result = buffer.getvalue()

    #         return {"output": exec_result} if exec_result else {"message": "OK"}
    #     except Exception as e:
    #         raise HTTPException(status_code=400, detail=str(e))
    if code_data.exit:
        shell.exit()
        return {"message": "exited"}
    return {"message": shell.execute(code_data.code)}
