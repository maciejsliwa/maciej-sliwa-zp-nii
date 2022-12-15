import http.client
import json
import os
from datetime import datetime
from shutil import rmtree
import cv2
import sympy
from fastapi import FastAPI, HTTPException, Depends, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

app = FastAPI()
MY_DOMAIN = os.environ.get('AUTH0_SRV', '')
PAYLOAD = os.environ.get('AUTH0_PAYLOAD', '')
TMP_DIR = "testfiles"
PATH_INPUT_IMG = "testfiles//{0}"
PATH_OUTPUT_IMG = "testfiles//inv_{0}"


def cleanup():
    rmtree(TMP_DIR)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.get("/prime/{number}")
async def is_prime_number(number: str):
    ret = {'return': ''}
    if number.isnumeric():
        ret['return'] = sympy.isprime(int(number))
    return ret


@app.get("/token")
async def get_token():
    conn = http.client.HTTPSConnection(MY_DOMAIN)
    headers = {'content-type': "application/json"}
    conn.request("POST", "/oauth/token", PAYLOAD, headers)
    res = conn.getresponse()
    data = json.loads(res.read().decode("utf-8"))
    if not res.status == 200:
        raise HTTPException(status_code=401, detail="Credentials invalid")
    else:
        return data['access_token']


@app.get("/time")
async def get_time(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    conn = http.client.HTTPSConnection(MY_DOMAIN)
    headers = {
        'content-type': "application/json",
        'authorization': f"Bearer {token.credentials}"
    }
    conn.request("GET", "/api/v2/clients", headers=headers)
    res = conn.getresponse()
    if not res.status == 200:
        raise HTTPException(status_code=401, detail="Token expired or invalid")
    else:
        return datetime.now().time()


@app.post("/picture/invert")
async def picture_inverting(file: UploadFile):
    contents = await file.read()
    path_input = PATH_INPUT_IMG.format(file.filename)
    path_output = PATH_OUTPUT_IMG.format(file.filename)
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    with open(path_input, "wb") as f:
        f.write(contents)
    img = cv2.imread(path_input)
    img_invert = cv2.bitwise_not(img)
    cv2.imwrite(path_output, img_invert)
    return FileResponse(path_output, background=BackgroundTask(cleanup))
