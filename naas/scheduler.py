from .ntypes import t_scheduler, t_output, t_add, t_update, t_delete
from .manager import Manager
import pandas as pd
import pretty_cron
import requests
import pycron


class Scheduler:
    naas = None
    role = t_scheduler
    manager = None

    def __init__(self):
        self.manager = Manager(t_scheduler)
        self.path = self.manager.path

    def list(self, path=None):
        return self.manager.list_prod("list_history", path)

    def list_output(self, path=None):
        return self.manager.list_prod("list_output", path)

    def get(self, path=None, histo=None):
        return self.manager.get_file(path, histo=histo)

    def get_output(self, path=None, histo=None):
        return self.manager.get_file(path, t_output, histo)

    def clear(self, path=None, histo=None):
        return self.manager.clear_file(path, None, histo)

    def clear_output(self, path=None, histo=None):
        return self.manager.clear_file(path, t_output, histo)

    def status(self):
        req = requests.get(url=f"{self.manager.naas_api}/scheduler")
        req.raise_for_status()
        jsn = req.json()
        print(jsn)
        return jsn

    def pause(self):
        req = requests.get(url=f"{self.manager.naas_api}/scheduler/pause")
        req.raise_for_status()
        jsn = req.json()
        print(jsn)
        return jsn

    def resume(self):
        req = requests.get(url=f"{self.manager.naas_api}/scheduler/resume")
        req.raise_for_status()
        jsn = req.json()
        print(jsn)
        return jsn

    def currents(self, raw=False):
        json_data = self.manager.get_naas()
        json_filtered = []
        for item in json_data:
            if item["type"] == self.role and item["status"] != t_delete:
                if raw:
                    json_filtered.append(item)
                else:
                    json_filtered.append({"path": item["path"], "value": item["value"]})
        if raw is False:
            df = pd.DataFrame(json_filtered)
            df = df.style.format({"value": pretty_cron.prettify_cron})
            return df
        return json_filtered

    def __check_cron(self, text):
        res = False
        try:
            pycron.is_now(text)
            res = True
        except ValueError:
            pass
        return res

    def add(self, path=None, recurrence=None, cron=None, params={}, debug=False):
        if self.manager.is_production():
            print("No add done, you are in production\n")
            return
        if recurrence:
            print("recurrence is deprecated use cron arg instead")
        cron = recurrence if recurrence else cron
        if not cron:
            print("No cron provided\n")
            return
        if not self.__check_cron(cron):
            print(f"WARNING : Recurrence wrong format {cron}")
            return
        current_file = self.manager.get_path(path)
        status = t_add
        try:
            self.manager.get_value(current_file, False)
            status = t_update
        except:  # noqa: E722
            pass
        self.manager.add_prod(
            {
                "type": self.role,
                "path": current_file,
                "status": status,
                "params": params,
                "value": cron,
            },
            debug,
        )
        cron_string = pretty_cron.prettify_cron(cron)
        print("👌 Well done! Your Notebook has been sent to production. \n")
        print(
            f'⏰ It will be scheduled "{cron_string}" (more on the syntax on https://crontab.guru/).\n'
        )
        print('Ps: to remove the "Scheduler", just replace .add by .delete')

    def delete(self, path=None, all=True, debug=False):
        if self.manager.is_production():
            print("No delete done, you are in production\n")
            return
        current_file = self.manager.get_path(path)
        self.manager.del_prod({"type": self.role, "path": current_file}, debug)
        print("🗑 Done! Your Scheduler has been remove from production.\n")
        if all is True:
            self.clear(current_file, "all")
            self.clear_output(current_file, "all")
