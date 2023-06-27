# Credit to cangcang-zcr@github - https://github.com/hwchase17/langchain/issues/2301
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any, Dict
import pexpect


class SandboxShell:

    def __init__(self, timeout: int = 10) -> None:
        self.subprocess: pexpect.spawn = None
        self.timeout = timeout

    def execute(self, command: str) -> str:
        if self.subprocess is None:
            process = pexpect.spawn(command + "\n")
            out = process.read_nonblocking(1000000, timeout=self.timeout)  # make sure this waits for command to finish
            if process.isalive():
                self.subprocess = process
        else:
            self.subprocess.send(command + "\n")
            out = self.subprocess.read_nonblocking(1000000, timeout=self.timeout)
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
