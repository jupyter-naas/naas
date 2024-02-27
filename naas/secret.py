from .ntypes import t_secret, t_add, t_delete, error_reject, error_busy
from .runner.env_var import n_env
import pandas as pd
import requests
import naas_python


class Secret:
    
    def __get_remote_secret(self, name: str):
        try:
            return naas_python.secret.get(name)
        except naas_python.domains.secret.SecretSchema.SecretNotFound:
            print("Secret not found")
            return False
        except:
            print("Secret get failed")
            return False
        
    def __create_remote_secret(self, name: str, value: str):
        try:
            naas_python.secret.create(name, value)
            return True
            # print("\nYour Secret has been moved to naas.ai 👌\n")
        except:
            print("Secret creation failed")
            return False
        
    def __create_remote_bulk_secret(self, secrets:str):
        try:
            naas_python.secret.bulk_create(secrets)
            return True
            # print("\nYour Secret has been moved to naas.ai 👌\n")
        except:
            print("Secret creation failed")
            return False
            
    def __delete_remote_secret(self, name:str):
        try:
            naas_python.secret.delete(name=name)
            return True
        except:
            #print("Secret not found")
            return False
            
    def __list_remote_secret(self):
        # try:
            return naas_python.secret.list()
        # except:
        #     print("Secret list failed")
        #     return False
        
    def list(self):
        local_secret = None
        remote_secret_list = self.__list_remote_secret()
        
        # convert remote secret to a dataframe
        remote_secret = pd.DataFrame(columns=['name', 'secret'])
        for secret in remote_secret_list:
            new_row = pd.DataFrame({'name': [secret.name], 'secret': [secret.value]})
            remote_secret = remote_secret.append(new_row, ignore_index=True)
            
        # local secret dataframe
        local_secret = self.__old_list()
        
        
        if local_secret.empty:
            return remote_secret

        local_secret = local_secret.drop("id", axis=1)
        local_secret = local_secret.drop("lastUpdate", axis=1)
        
        merged_secrets_df = pd.merge(remote_secret, local_secret, how='outer', indicator=True)
        
        # If the secret exists locally AND in api.naas.ai, I remove the local version of the secret.
        selected_secrets = merged_secrets_df[merged_secrets_df['_merge'] == "both"]
        for index, row in selected_secrets.iterrows():
            self.__old_delete(row['name'])
    
        # If the secret exists locally and does not exists in api.naas.ai, I create it in api.naas.ai and I delete the local version.
        secrets_list=[]
        selected_secrets = merged_secrets_df[merged_secrets_df['_merge'] == "right_only"]
        for index, row in selected_secrets.iterrows():
            # self.__create_remote_secret(name=row['name'], value=row['secret'])
            name = row['name']
            value = row['secret']
            new_secret = { "name": name, "value": value }
            secrets_list.append(new_secret)
            
            
            new_row = pd.DataFrame({'name': [row['name']], 'secret': [row['secret']]})
            remote_secret = remote_secret.append(new_row, ignore_index=True)
            
            self.__old_delete(row['name'])
        self.__create_remote_bulk_secret({"secrets":secrets_list})
        
        return remote_secret
        
    def __old_list(self, raw=False):
        try:
            r = requests.get(f"{n_env.api}/{t_secret}")
            r.raise_for_status()
            res = r.json()
            if raw:
                return res
            else:
                return pd.DataFrame.from_records(res)
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise

    def add(self, name=None, secret=None):
        if name is None or secret is None:
            return ("Incomplete secret")
        self.__create_remote_secret(name=name, value=secret)
        self.__old_delete(name)

    def get(self, name=None, default_value=None):
        all_secret = self.__old_list(True)
        local_secret = None
        remote_secret = None
        
        # Find local_secret
        for item in all_secret:
            if name == item["name"]:
                local_secret = item
                break  
        
        # try:
        remote_secret = self.__get_remote_secret(name=name)
        # except:
        #     print("Try Again")
        #     return None
    
        #if the secret exists on api.naas.ai
        # AND exists locally, then I remove the local version.   
        if remote_secret is not None and local_secret is not None:
            if  remote_secret.name == local_secret["name"]:
                self.__old_delete(name=local_secret["name"])
                return remote_secret.value
                
        #If the secret does not exists on api.naas.ai
        #If the secret exists locally
        #I take the local secret and create it on api.naas.ai.
        #I delete the local version of the secret.
        elif remote_secret is None and local_secret is not None:
            self.__create_remote_secret(local_secret["name"], local_secret["secret"])
            secret = self.__get_remote_secret(local_secret["name"])
            self.__old_delete(name=local_secret["name"])
            return secret.value
            
        else: # local_secret is None
            # If the secret exists on api.naas.ai 
            # I use that value
            if remote_secret is not None :
                return remote_secret.value
        return default_value
    
    def __old_get(self, name=None, default_value=None):
        all_secret = self.__old_list(True)
        secret_item = None
        for item in all_secret:
            if name == item["name"]:
                secret_item = item
                break
        if secret_item is not None:
            return secret_item.get("secret", None)
        return default_value

    def delete(self, name=None):
        if name is None:
            return ("Incomplete name")
        self.__delete_remote_secret(name=name)
        self.__old_delete(name
                        )
    def __old_delete(self, name=None):
        obj = {"name": name, "secret": "", "status": t_delete}
        try:
            r = requests.post(f"{n_env.api}/{t_secret}", json=obj)
            r.raise_for_status()
            # print("👌 Well done! Your Secret has been remove in production. \n")
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise

    def __old_add(self, name=None, secret=None):
        obj = {"name": name, "secret": secret, "status": t_add}
        try:
            r = requests.post(f"{n_env.api}/{t_secret}", json=obj)
            r.raise_for_status()
            print("👌 Well done! Your Secret has been sent to production. \n")
            print('PS: to remove the "Secret" feature, just replace .add by .delete')
        except requests.exceptions.ConnectionError as err:
            print(error_busy, err)
            raise
        except requests.exceptions.HTTPError as err:
            print(error_reject, err)
            raise