import urllib3, requests, json, os, re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TixatiServer:
    TRANSFERS_PAGE_HTML_SCRAPER = re.compile("[\S\s]*?<tr class=\"(downloading|complete|seeding|offline)_(?:odd|even)\">[\S\s]*?<td><a href=\"\/transfers\/([a-z0-9]+)\/details\">([\S\s]*?)<\/a><\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\d]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<\/tr>")

    class Transfer:
        def __init__(self, tuple_entry):
            self.StatusClass = tuple_entry[0]
            self.Id = tuple_entry[1]
            self.Title = tuple_entry[2]
            self.SizeLeft = tuple_entry[3]
            self.Percent = tuple_entry[4]
            self.Status = tuple_entry[5]
            self.BytesIn = tuple_entry[6]
            self.BytesOut = tuple_entry[7]
            self.Priority = tuple_entry[8]
            self.TimeLeft = tuple_entry[9]

    def FetchTransfers(self) -> list:
        constructed_url:str = "{address}:{port}/transfersscrape".format(address=self.Address, port=self.Port)
        response = requests.get(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), verify=False)
        regex_results = self.TRANSFERS_PAGE_HTML_SCRAPER.findall(response.content.decode())

        if isinstance(regex_results, list):
            return [self.Transfer(transfer_tuple) for transfer_tuple in regex_results]
        else:
            raise TypeError("Regex parsing results returned None. Failed to scrape using current Regex.")

    def AddTransfer(self, magnet_link:str) -> requests.Response:
        constructed_url:str = "{address}:{port}/transfers/action".format(address=self.Address, port=self.Port)

        return requests.post(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), files={
            'addlinktext': magnet_link,
            'addlink': "Add"
        }, verify=False)

    def RemoveTransfer(self, transfer_id:str) -> requests.Response:
        constructed_url:str = "{address}:{port}/transfers/{transfer_id}/details/action".format(address=self.Address, port=self.Port, transfer_id=transfer_id)

        return requests.post(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), data={
            transfer_id:"1",
            "removeconf":"Remove Transfers"
        }, verify=False)

    def DeleteTransfer(self, transfer_id:str) -> requests.Response:
        constructed_url:str = "{address}:{port}/transfers/action".format(address=self.Address, port=self.Port)

        return requests.post(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), data={
            transfer_id: "1",
            "deleteconf": "Delete Transfers And Downloaded Files"
        }, verify=False)

    def StartTransfer(self, transfer_id:str) -> requests.Response:
        constructed_url:str = "{address}:{port}/transfers/{transfer_id}/details/action".format(address=self.Address, port=self.Port, transfer_id=transfer_id)
        return requests.post(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), data={"start": "Start"}, verify=False)

    def StopTransfer(self, transfer_id:str) -> requests.Response:
        constructed_url:str = "{address}:{port}/transfers/{transfer_id}/details/action".format(address=self.Address, port=self.Port, transfer_id=transfer_id)
        return requests.post(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), data={"stop": "Stop"}, verify=False)

    def CheckFiles(self, transfer_id:str) -> requests.Response:
        constructed_url:str = "{address}:{port}/transfers/{transfer_id}/details/action".format(address=self.Address, port=self.Port, transfer_id=transfer_id)
        return requests.post(constructed_url, auth=requests.auth.HTTPDigestAuth(self.Username, self.Password), data={"checkfiles": "Check Files"}, verify=False)

    def __init__(self, config):
        # Config points to a config.json file, and must be parsed into a dict before moving on.
        if isinstance(config, str) and config.endswith('.json') and os.path.isfile(config):
            with open(config, "rb") as io:
                config = json.load(io)

        if isinstance(config, dict):
            try:
                if isinstance(config["address"], str): self.Address = config["address"]
                else: raise TypeError("The 'address' key is of an invalid type. Is ({0}), expected str.".format(str(type(config["address"]))))

                if isinstance(config["username"], str): self.Username = config["username"]
                else: raise TypeError("The 'username' key is of an invalid type. Is ({0}), expected str.".format(str(type(config["username"]))))

                if isinstance(config["password"], str):
                    self.Password = config["password"]

                    # If no password was supplied in the config, prompt for one instead.
                    if self.Password == "":
                        self.Password = input("Enter Server Password: ")
                else:
                    raise TypeError("The 'password' key is of an invalid type. Is ({0}), expected str.".format(str(type(config["password"]))))

                if isinstance(config["port"], int): self.Port = config["port"]
                else: raise TypeError("The 'port' key is of an invalid type. Is ({0}), expected int.".format(int(type(config["port"]))))
            except Exception as exception:
                print("Could not construct TixatiServer instance due to an exception. Re-raising exception.")
                raise exception
        else:
            raise TypeError("The 'config' parameter is neither a string pointing to a config file, nor a dict containing the config values.")
