# Credit to cangcang-zcr@github - https://github.com/hwchase17/langchain/issues/2301
FROM python:3.10

# RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U \
#     && pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

RUN pip install fastapi
RUN pip install uvicorn
RUN pip install pydantic
RUN pip install pexpect

COPY scripts/run_sandbox.py /app/
WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "run_sandbox:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]