from fastapi import FastAPI, HTTPException, Form
import requests
import httpx
import asyncio

app = FastAPI()

async def send_login_request_to_eskiz(email: str, password: str) -> dict:
    url = "https://notify.eskiz.uz/api/auth/login"
    data = {
        "email": email,
        "password": password
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=data)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return response.json()
    except httpx.HTTPStatusError as exc:
        print(f"Request data: {data}")
        print(f"Response status: {exc.response.status_code}")
        print(f"Response text: {exc.response.text}")
        raise HTTPException(status_code=exc.response.status_code, detail=f"Eskiz API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")


# async def send_sms_eskiz(token: str, mobile_phone: str, message: str) -> dict:
#     url = "https://notify.eskiz.uz/api/message/sms/send"
#     headers = {
#         'Authorization': f"Bearer {token}"
#     }
#     data = {
#         'mobile_phone': f"998{mobile_phone}",
#         'message': f"Your verification code is: {message}",
#         'from': "Maxsus texnika"
#     }
#
#     data['callback_url'] = "http://0000.uz/test.php"
#
#     try:
#         async with httpx.AsyncClient() as client:
#             response = await client.post(url, headers=headers, data=data)
#             response.raise_for_status()  # Raise an exception for 4xx/5xx responses
#             return response.json()
#     except httpx.HTTPStatusError as exc:
#         print(f"Request data: {data}")
#         print(f"Response status: {exc.response.status_code}")
#         print(f"Response text: {exc.response.text}")
#         raise HTTPException(status_code=exc.response.status_code, detail=f"Eskiz API error: {exc.response.text}")
#     except Exception as exc:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")


async def refresh_token_eskiz(refresh_token: str) -> dict:
    url = "https://notify.eskiz.uz/api/auth/refresh"
    data = {
        "refresh_token": refresh_token
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.patch(url, data=data)
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            return response.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=f"Eskiz API error: {exc.response.text}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}")



def send_message(phone, code,token_sms):
    send_url = "https://notify.eskiz.uz/api/message/sms/send"
    token = token_sms
    headers = {
        'Authorization': f'Bearer {token}'
    }
    # Vash kod podtverjdeniya dlya mobilnogo prilojeniya Avtoritet Group:
    data = {
        'mobile_phone': phone[1:],
        'message': f"<#> Your verification code: {code}",
        'from': 'xxxx'
    }

    resp = requests.post(url=send_url, data=data, headers=headers)

    # print(resp.status_code, resp.text)

    if resp.status_code == 401:
        token = refresh_token_eskiz(token_sms)

        headers = {
            'Authorization': f'Bearer {token}'
        }
        resp = requests.post(url=send_url, data=data, headers=headers)
    print(resp.status_code, resp.text)

    return resp

async def main():
    try:
        result = await send_login_request_to_eskiz("fayzulloevasadbek@gmail.com", "zVNnLo76p9g4WJIN6lIdliHdGjoroyOnpHgsTvFT")
        print(result['data']['token'])
        token_sms = result['data']['token']
        print(send_message("+998993590562","4556",token_sms))

    except HTTPException as exc:
        print(f"HTTP Exception: {exc.detail}")

# Run the main function to test
if __name__ == "__main__":
    asyncio.run(main())
