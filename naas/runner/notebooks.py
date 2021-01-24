from naas.types import (
    t_notebook,
    t_scheduler,
    t_error,
    t_output,
    guess_ext,
    mime_json,
    mime_html,
    mime_md,
    mime_text,
    mime_csv,
    mime_jpeg,
    mime_png,
    mime_list,
)
from nbconvert import HTMLExporter
from sanic import response
from .env_var import n_env
import papermill as pm
import traceback
import mimetypes
import datetime
import shutil
import base64
import json
import time
import bs4
import csv
import os
import io


kern_manager = None

try:
    from enterprise_gateway.services.kernels.remotemanager import RemoteKernelManager

    kern_manager = RemoteKernelManager
except ImportError:
    pass


class Notebooks:
    __logger = None
    __notif = None
    __html_exporter = None

    def __init__(self, logger, notif=None):
        self.__logger = logger
        self.__notif = notif
        self.__html_exporter = HTMLExporter()
        self.__html_exporter.template_name = "lab"

    def response(self, uid, filepath, res, duration, params):
        next_url = params.get("next_url", None)
        if next_url is not None and "https://" not in next_url:
            self.__logger.error(
                {
                    "id": uid,
                    "type": t_notebook,
                    "status": "next_url",
                    "filepath": filepath,
                    "url": next_url,
                    "error": "url not in right format",
                }
            )
        if next_url is not None and "https" in next_url:
            self.__logger.info(
                {
                    "id": uid,
                    "type": t_notebook,
                    "status": "next_url",
                    "filepath": filepath,
                    "url": next_url,
                }
            )
            return response.redirect(next_url)
        else:
            res_data = self.__get_res(res, filepath)
            if res_data and res_data.get("type"):
                file_name = os.path.basename(filepath)
                ext = res_data.get("ext")
                inline = params.get("inline", False)
                headers = dict()
                new_file_name = f'{file_name.split(".")[0]}{ext}'
                if ext and not inline:
                    headers[
                        "Content-Disposition"
                    ] = f'attachment; filename="{new_file_name}"'
                else:
                    headers["Content-Type"] = res_data.get("type")

                async def streaming_fn(res):
                    # await res.write(str(res_data.get("data").decode('UTF-8')))
                    await res.write(res_data.get("data"))

                return response.stream(
                    streaming_fn,
                    headers=headers,
                    content_type=mimetypes.guess_type(new_file_name)[0],
                )
            else:
                return response.json({"id": uid, "status": "Done", "time": duration})

    def __convert_csv(self, data):
        soup = bs4.BeautifulSoup(data, features="html5lib")
        output = []
        for table_num, table in enumerate(soup.find_all("table")):
            csv_string = io.StringIO()
            csv_writer = csv.writer(
                csv_string, delimiter=";", lineterminator="\n", quoting=csv.QUOTE_ALL
            )
            for tr in table.find_all("tr"):
                row = [
                    "".join(cell.stripped_strings) for cell in tr.find_all(["td", "th"])
                ]
                csv_writer.writerow(row)
            table_attrs = dict(num=table_num)
            output.append((csv_string.getvalue(), table_attrs))
        return output[0][0]

    def get_out_path(self, path):
        filename = os.path.basename(path)
        dirname = os.path.dirname(path)
        out_path = os.path.join(dirname, f"{t_output}__{filename}")
        return out_path

    def __nb_render(self, filepath):
        result_type = None
        result = None
        try:
            result_type = mime_html
            file_filepath_out = self.get_out_path(filepath)
            (result, ressources) = self.__html_exporter.from_filename(file_filepath_out)
        except FileNotFoundError:
            tb = traceback.format_exc()
            result_type = mime_json
            result = {
                "error": "output file not found",
                "trace": tb,
            }
        result_ext = guess_ext(result_type)
        return result_type, result_ext, result

    def __nb_file(self, meta, data):
        result_type = None
        result = None
        try:
            result_type = meta.get("naas_type")
            path = data.get(mime_json).get("path")
            with open(path, "r") as f:
                result = f.read()
                f.close()
        except FileNotFoundError:  # noqa: E722
            result_type = mime_json
            result = {"error": "file not found"}
        result_ext = guess_ext(result_type)
        return result_type, result_ext, result

    def __check_output(self, output, filepath):
        metadata = output.get("metadata", [])
        data = output.get("data", dict())
        meta_filtered = list(
            filter(lambda meta: metadata[meta].get("naas_api"), metadata)
        )
        for meta in meta_filtered:
            if data.get(mime_md) and metadata[meta].get("naas_type") == t_notebook:
                return self.__nb_render(filepath)
            elif data.get(mime_json) and metadata[meta].get("naas_type"):
                return self.__nb_file(metadata[meta], data)
            elif data.get(mime_html) and metadata[meta].get("naas_type") == "markdown":
                result_ext = guess_ext(mime_html)
                return mime_html, result_ext, data.get(mime_html)
            elif data.get(mime_html) and metadata[meta].get("naas_type") == "text":
                result_ext = guess_ext(mime_text)
                return mime_text, result_ext, data.get(mime_html)
            elif data.get(mime_html) and metadata[meta].get("naas_type") == "csv":
                result_ext = guess_ext(mime_csv)
                return mime_csv, result_ext, self.__convert_csv(data.get(mime_html))
            elif data.get(mime_json):
                result_ext = guess_ext(mime_json)
                return mime_json, result_ext, json.dumps(data.get(mime_json))
            elif data.get(mime_jpeg):
                im_byt = io.BytesIO(base64.b64decode(data.get(mime_jpeg)))
                result_ext = guess_ext(mime_jpeg)
                return mime_jpeg, result_ext, im_byt.getvalue()
            elif data.get(mime_png):
                im_byt = io.BytesIO(base64.b64decode(data.get(mime_png)))
                result_ext = guess_ext(mime_png)
                return mime_png, result_ext, im_byt.getvalue()
            else:
                result_type = next((i for i in mime_list if data.get(i)), None)
                result_ext = guess_ext(result_type)
                return result_type, result_ext, data.get(result_type)
        return None, None, None

    def __get_res(self, res, filepath):
        cells = res.get("cells")
        for cell in cells:
            outputs = cell.get("outputs", [])
            for output in outputs:
                (result_type, result_ext, result) = self.__check_output(
                    output, filepath
                )
                if result is not None and result_type is not None:
                    return {"type": result_type, "ext": result_ext, "data": result}
        return None

    def __keep_out_history(self, file_filepath_out):
        if os.path.exists(file_filepath_out):
            try:
                out_finename = os.path.basename(file_filepath_out)
                out_dir = os.path.dirname(file_filepath_out)
                history_filename = f'{datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")}___{out_finename}'
                history_path = os.path.join(out_dir, history_filename)
                shutil.copy(file_filepath_out, history_path)
            except:  # noqa: E722
                pass

    def __pm_exec(self, uid, file_dirpath, file_filepath, file_filepath_out, params):
        res = None
        if kern_manager:
            res = pm.execute_notebook(
                input_path=file_filepath,
                output_path=file_filepath_out,
                progress_bar=False,
                cwd=file_dirpath,
                parameters=params,
                kernel_manager_class=kern_manager,
            )
        else:
            res = pm.execute_notebook(
                input_path=file_filepath,
                output_path=file_filepath_out,
                progress_bar=False,
                cwd=file_dirpath,
                parameters=params,
            )
        if not res:
            res = {"uid": uid, "error": "Unknow error", "duration": 0}
        self.__keep_out_history(file_filepath_out)
        return res

    def __send_notification(self, uid, res, file_filepath, current_type, value, params):
        notif_down = params.get("notif_down", None)
        notif_up = params.get("notif_up", None)
        small_path = file_filepath.replace(n_env.server_root, "")
        if res.get("error"):
            if n_env.user is not None:
                self.__notif.send_status(
                    uid, "down", n_env.user, small_path, current_type, value
                )
            if notif_down and self.__notif:
                self.__notif.send_status(
                    uid, "down", notif_down, small_path, current_type, value
                )
        elif notif_up and current_type == t_scheduler and self.__notif:
            self.__notif.send_status(
                uid, "up", notif_down, small_path, current_type, value
            )
        elif notif_up and self.__notif:
            self.__notif.send_status(uid, "up", notif_up, small_path, current_type)

    def __get_output_path(self, file_filepath):
        file_dirpath = os.path.dirname(file_filepath)
        file_filename = os.path.basename(file_filepath)
        file_filepath_out = os.path.join(file_dirpath, f"{t_output}__{file_filename}")
        return file_filepath_out

    async def exec(self, uid, job):
        value = job.get("value", None)
        current_type = job.get("type", None)
        file_filepath = job.get("path")
        if not os.path.exists(file_filepath):
            err = "file not found"
            self.__logger.error(
                {
                    "id": uid,
                    "type": "filepath",
                    "status": t_error,
                    "filepath": file_filepath,
                    "error": err,
                }
            )
            return {"error": err, "duration": 0}
        file_dirpath = os.path.dirname(file_filepath)
        file_filepath_out = self.__get_output_path(file_filepath)
        params = job.get("params", dict())
        params["naas_uid"] = uid
        params["naas_runtime"] = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        params["naas_env"] = "PRODUCTION"
        start_time = time.time()
        res = None
        try:
            res = self.__pm_exec(
                uid, file_dirpath, file_filepath, file_filepath_out, params
            )
        except pm.PapermillExecutionError as err:
            tb = traceback.format_exc()
            res = {"error": err, "traceback": str(tb)}
            self.__logger.error(
                {
                    "id": uid,
                    "type": "PapermillExecutionError",
                    "status": t_error,
                    "filepath": file_filepath,
                    "output_filepath": file_filepath_out,
                    "error": str(err),
                }
            )
        except pm.PapermillException as err:
            tb = traceback.format_exc()
            res = {"error": err, "traceback": str(tb)}
            self.__logger.error(
                {
                    "id": uid,
                    "type": "Exception",
                    "status": t_error,
                    "filepath": file_filepath,
                    "output_filepath": file_filepath_out,
                    "error": err,
                    "traceback": str(tb),
                }
            )

        except RuntimeError as err:
            tb = traceback.format_exc()
            res = {"error": err, "traceback": str(tb)}
            self.__logger.error(
                {
                    "id": uid,
                    "type": "Exception",
                    "status": t_error,
                    "filepath": file_filepath,
                    "output_filepath": file_filepath_out,
                    "error": err,
                    "traceback": str(tb),
                }
            )
        except:  # noqa: E722
            tb = traceback.format_exc()
            res = {"error": "Unknow error", "traceback": str(tb)}
            self.__logger.error(
                {
                    "id": uid,
                    "type": "Exception",
                    "status": t_error,
                    "filepath": file_filepath,
                    "output_filepath": file_filepath_out,
                    "error": res.get("error"),
                    "traceback": str(tb),
                }
            )
        res["duration"] = time.time() - start_time
        try:
            self.__send_notification(
                uid, res, file_filepath_out, current_type, value, params
            )
        except ConnectionError as err:
            self.__logger.error(
                {
                    "id": uid,
                    "type": "Exception",
                    "status": t_error,
                    "filepath": file_filepath,
                    "output_filepath": file_filepath_out,
                    "error": "Cannot send notification",
                    "traceback": str(err),
                }
            )
        return res
