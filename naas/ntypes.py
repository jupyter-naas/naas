from IPython.core.display import Javascript, display, HTML
import ipywidgets as widgets
import mimetypes

t_notebook = "notebook"
t_asset = "asset"
t_downloader = "downloader"
t_dependency = "dependency"
t_scheduler = "scheduler"

t_secret = "secret"

t_tz = "timezone"
t_performance = "performance"
t_job = "job"
t_job_not_found = "job not found"
t_env = "env"
t_log = "log"

t_storage = "storage"
t_cpu = "cpu"
t_ram = "ram"

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


def copy_clipboard():
    js = """
    if (!window.copyToClipboard) {
        window.copyToClipboard = (text) => {
            const dummy = document.createElement("textarea");
            document.body.appendChild(dummy);
            dummy.value = text;
            dummy.select();
            document.execCommand("copy");
            document.body.removeChild(dummy);
        }
    }
    """
    display(Javascript(js))


def copy_button_df(text, title="Copy URL"):
    return f"""<button class="lm-Widget p-Widget jupyter-widgets jupyter-button widget-button mod-primary"
        title="{title}"
        onclick="window.copyToClipboard('{text}')">{title}</button>"""


def link_df(val):
    # target _blank to open new window
    return f'<a target="_blank" href="{val}">{val}</a>'


def copy_button(text, title="Copy URL"):
    copy_clipboard()
    button = widgets.Button(description=title, button_style="primary")
    output = widgets.Output()

    def on_button_clicked(b):
        with output:
            html_div = f'<script>window.copyToClipboard("{text}");</script><div id="pasting_to_clipboard">✅ Copied !</div>'
            display(HTML(html_div))

    button.on_click(on_button_clicked)
    display(button, output)
