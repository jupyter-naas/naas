from IPython.core.display import display, HTML
import ipywidgets as widgets
import mimetypes
import uuid

t_notebook = "notebook"
t_asset = "asset"
t_downloader = "downloader"
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
t_main = "main"

t_add = "installed"
t_delete = "delete"
t_update = "edited"
t_start = "started"
t_busy = "busy"
t_skip = "skiped"
t_error = "error"
t_health = "healthy"

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


def copy_clipboard(text):
    uid = uuid.uuid4().hex
    js = """<script>
    function copyToClipboard_{uid}(text) {
        const dummy = document.createElement("textarea");
        document.body.appendChild(dummy);
        dummy.value = text;
        dummy.select();
        document.execCommand("copy");
        document.body.removeChild(dummy);
    }
    </script>"""
    js = js.replace("{uid}", uid)
    display(HTML(js))
    js2 = f"<script>copyToClipboard_{uid}(`" + text + "`);</script>"
    display(HTML(js2))


def copy_button(text, title="Copy URL"):
    button = widgets.Button(description=title, button_style="primary")
    output = widgets.Output()

    def on_button_clicked(b):
        with output:
            copy_clipboard(text)
            html_div = '<div id="pasting_to_clipboard">✅ Copied !</div>'
            display(HTML(html_div))

    button.on_click(on_button_clicked)
    display(button, output)
