# Credit to cangcang-zcr@github - https://github.com/hwchase17/langchain/issues/2301
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict
import pexpect
from datetime import datetime, timedelta
import time

READ_BUFFER = 1_000_000


def poll_for_output(
    process: pexpect.spawn,
    poll_time: float = 0.2,
    idle_timeout: float = 5.0,
    hard_timeout: float = 30.0,
) -> str:
    end_time = datetime.utcnow() + timedelta(seconds=hard_timeout)
    output = b""
    while True:
        remaining_time = (end_time - datetime.utcnow()).total_seconds()
        try:
            output += process.read_nonblocking(READ_BUFFER, timeout=min(remaining_time, idle_timeout))
        except pexpect.exceptions.TIMEOUT:
            return output
        except pexpect.exceptions.EOF:
            return output
        remaining_time = (end_time - datetime.utcnow()).total_seconds()
        if remaining_time <= poll_time:
            return output
        time.sleep(poll_time)


class SandboxShell:

    def __init__(self, timeout: int = 10) -> None:
        self.subprocess: pexpect.spawn = None
        self.timeout = timeout

    def execute(self, command: str) -> str:
        if self.subprocess is None:
            process = pexpect.spawn(command + "\n")
            out = poll_for_output(process)
            if process.isalive():
                self.subprocess = process
        else:
            self.subprocess.send(command + "\n")
            out = poll_for_output(self.subprocess)
            if not self.subprocess.isalive():
                self.subprocess.close()
                self.subprocess = None
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
