import mimetypes

t_notebook = "notebook"
t_asset = "asset"
t_dependency = "dependency"
t_scheduler = "scheduler"
t_secret = "secret"

t_tz = "timezone"
t_job = "job"
t_env = "env"
t_log = "log"

t_list_output = "list_output"
t_list_histo = "list_histo"
t_output = "output"
t_production = "prod"
t_histo = "history"
t_list = "list"
t_send = "send"
t_add = "installed"
t_delete = "delete"
t_update = "edited"
t_start = "started"
t_busy = "busy"
t_skip = "skiped"
t_error = "error"
t_health = "healthy"
t_main = "main"

mime_html = "text/html"
mime_csv = "text/csv"
mime_html = "text/html"
mime_md = "text/markdown"
mime_text = "text/plain"
mime_json = "application/json"
mime_nb = "application/vnd.jupyter"
mime_jpeg = "image/jpeg"
mime_png = "image/png"
mime_svg = "image/svg+xml"
mime_list = [mime_html, mime_svg]

error_busy = "Naas look busy, try to reload your machine"
error_reject = "Naas refused your request, reason :"


def guess_type(filepath):
    result_type = mimetypes.guess_type(filepath)[0]
    if result_type is None and filepath.endswith(".ipynb"):
        result_type = mime_nb
    return result_type


def guess_ext(cur_type):
    result_ext = mimetypes.guess_extension(cur_type, strict=False)
    if result_ext is None and cur_type == mime_nb:
        result_ext = ".ipynb"
    return result_ext
