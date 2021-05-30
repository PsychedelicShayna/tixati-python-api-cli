import urllib3, requests, json, os, re

# When making HTTPS requests, certificate verification is always disabled (verify=False) due to Tixati using self-signed certificates.
# This supresses urllib from spitting out insecure request warnings in the console.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class TixatiServer:
    # The hefty piece of RegEx used to scrape the transfers page.
    TRANSFERS_PAGE_HTML_SCRAPER = re.compile("[\S\s]*?<tr class=\"(downloading|complete|seeding|offline|queued)_(?:odd|even)\">[\S\s]*?<td><a href=\"\/transfers\/([a-z0-9]+)\/details\">([\S\s]*?)<\/a><\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\d]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<td>([\S\s]*?)<\/td>[\S\s]*?<\/tr>")

    class Transfer:
        def __init__(self, values:tuple):
            if not isinstance(values, tuple):
                raise TypeError("The 'values' parameter is of an invalid type. Expected a tuple, received {0}".format(type(values)))

            if len(values) == 10:
                self.StatusClass    = values[0]
                self.Id             = values[1]
                self.Title          = values[2]
                self.SizeLeft       = values[3]
                self.Percent        = values[4]
                self.Status         = values[5]
                self.BytesIn        = values[6]
                self.BytesOut       = values[7]
                self.Priority       = values[8]
                self.TimeLeft       = values[9]
            else:
                raise IndexError("Insufficient data in tuple to construct a Transfer instance. Expected 10 values, received {length} values.".format(length = len(values)))

    def fetch_transfers(self) -> list:
        request_url:str = "{address}:{port}/transfersscrape".format(address=self.address, port=self.port)
        response = requests.get(request_url, auth=requests.auth.HTTPDigestAuth(self.username, self.password), verify=False)

        if response.status_code != 200:
            raise requests.exceptions.HTTPError("HTTP Status Code {status_code} != 200".format(status_code = response.status_code))

        regex_results = self.TRANSFERS_PAGE_HTML_SCRAPER.findall(response.content.decode())

        if not (isinstance(regex_results, list) and len(regex_results)):
            raise TypeError("RegEx scraping yielded no results, something broke. RegEx results: {results}".format(results = regex_results))

        return [self.Transfer(transfer_tuple) for transfer_tuple in regex_results]

    def _urlencoded_request(self, method, target:str, data:dict, expected_status_code:int = 200) -> requests.Response:
        request_url:str = "{address}:{port}{target}".format(address = self.address, port=self.port, target=target)
        response = method(request_url, auth=requests.auth.HTTPDigestAuth(self.username, self.password), data=data, verify=False)

        if expected_status_code not in (None, response.status_code):
            raise requests.exceptions.HTTPError("HTTP Status Code {status_code} != {expected_status_code}".format(
                status_code = response.status_code,
                expected_status_code = expected_status_code
            ))

        return response

    def _multipart_request(self, method, target:str, files:dict, expected_status_code:int = 200) -> requests.Response:
        request_url:str = "{address}:{port}{target}".format(address = self.address, port=self.port, target=target)
        response = method(request_url, auth=requests.auth.HTTPDigestAuth(self.username, self.password), files=files, verify=False)

        if expected_status_code not in (None, response.status_code):
            raise requests.exceptions.HTTPError("HTTP Status Code {status_code} != {expected_status_code}".format(
                status_code = response.status_code,
                expected_status_code = expected_status_code
            ))

        return response

    def add_transfer(self, magnet_link:str) -> requests.Response:
        return self._multipart_request(requests.post, "/transfers/action", {"addlinktext": magnet_link, "addlink": "Add"})

    def remove_transfer(self, transfer_id:str) -> requests.Response:
        return self._urlencoded_request(requests.post, "/transfers/{0}/details/action".format(transfer_id), data={transfer_id:"1", "removeconf":"Remove Transfers"})

    def delete_transfer(self, transfer_id:str) -> requests.Response:
        return self._urlencoded_request(requests.post, "/transfers/action", {transfer_id:"1", "deleteconf": "Delete Transfers And Downloaded Files"})

    def start_transfer(self, transfer_id:str) -> requests.Response:
        return self._urlencoded_request(requests.post, "/transfers/{0}/details/action".format(transfer_id), {"start":"Start"})

    def stop_transfer(self, transfer_id:str) -> requests.Response:
        return self._urlencoded_request(requests.post, "/transfers/{0}/details/action".format(transfer_id), {"stop":"Stop"})

    def check_files(self, transfer_id:str) -> requests.Response:
        return self._urlencoded_request(requests.post, "/transfers/{0}/details/action".format(transfer_id), {"checkfiles":"Check Files"})

    def __init__(self, config):
        # Config variable might be a string pointing to a JSON file, if so, load the JSON into the config variable as a dict.
        if isinstance(config, str) and config.endswith('.json') and os.path.isfile(config):
            with open(config, "rb") as io:
                config = json.load(io)

        # Ensure all config keys are present, and hold the right value types.
        if isinstance(config, dict):
            for required_key in [("address", str), ("port", int), ("username", str), ("password", str)]:
                if required_key[0] in config:
                    if not isinstance(config[required_key[0]], required_key[1]):

                        # Exception raised if the value of a required config key is of the wrong type.
                        raise TypeError("The config value of '{key}' is of an invalid type, expected {expected_type}, got {value_type}".format(
                            key=required_key[0], expected_type=required_key[1], value_type=type(config[required_key[0]])
                        ))
                else:
                    # Exception raised if required key is missing from config.
                    raise KeyError("Cannot construct TixatiServer instance; the config dict is missing a required value: '{key}'".format(key = required_key[0]))
        else:
            # Exception raised if config isn't a dict / hasn't been converted into one from a str.
            raise TypeError("The 'config' parameter is neither a string pointing to a config file, nor a dict containing the config values.")

        self.address:str   =  config["address"]
        self.port:int      =  config["port"]
        self.username:str  =  config["username"]
        self.password:str  =  config["password"]
