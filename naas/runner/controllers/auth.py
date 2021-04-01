from naas.runner.env_var import n_env
import requests


def get_hub_user(request):
    try:
        headers = (
            {
                "content-type": "application/json",
                "authorization": request.headers.get("authorization", None),
            },
        )
        req = requests.get(url=f"{n_env.hub_base}/hub/api/user", headers=headers)
        req.raise_for_status()
        jsn = req.json()
        return jsn
    except:  # noqa: E722
        return None
