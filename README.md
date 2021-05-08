# Tixati Python API and Command Line Interface
This project consists of two parts: `tixati_api.py` which is a general purpose API class for interfacing with Tixati's webserver through Python, and `tixcli.py` which is a command line interface that implements `tixati_api.py` to be able to manage torrents/transfers remotely from the command line. You will need to have Tixati's webserver up and running to be able to use this.

Since this script is using RegEx to scrape the transfer list, it's not going to be compatible with every HTML template / theme you have set up for your web interface. This is tested and works with [Alduin94's tixati-dark-theme](https://github.com/Alduin94/tixati-dark-theme) - but does not work with the default theme. I'm going to try to find a more elegant way of fetching the transfer list in the future, but for now if you wish to use this script as is, then you'll have to use Alduin's theme or modify the RegeEx to accomodate the theme that you're using.


You must create a `config.json` file within the same directory as `tixcli.py` in order not to be prompted for a server/port/username/password every time you run the command. See the notes section of the help text for more information as to the format.

## Help Text
```
General Operations
   --help (-h)                                  | This help text.

   --list (-l) [all | <filter>:<filter>..]      | Lists all transfers if "all" is specified, otherwise filters using a whitelist.

        <filter> could be...
                    name=<name> -- Filters for transfers with <name> included in the title.

                    offline     -- Includes offline transfers.
                    completed   -- Includes completed transfers.
                    seeding     -- Includes seeding transfers.
                    downloading -- Includes downloading transfers.

                    id          -- A special switch that prints out the transfer IDs as a ; separated list for use
                                   with transfer operations, can be piped into clip for immediate copying.


Transfer Operations
    --start (-st) <id;id;id..>                | Starts one or more transfers with the given IDs.
    --stop  (-sp) <id;id;id..>                | Stops one or more transfers with the given IDs.
    --delete (-d) <id;id;id..>                | Removes and deletes the files of one or more transfers with the given IDs.
    --remove (-r) <id;id;id..>                | Removes one or more transfers with the given IDs.

Example Usage
    tixcli -l seeding:name=Toradora
        | Lists all transfers that are currently seeding and contain "Toradora" in the title.

    tixcli -l downloading:seeding:id | clip
        | Prints out a ; separated list of all the transfer IDs that are currently downloading or seeding,
        | before getting piped into the clipboard. Without piping into the clipboard, the output would look like
        | '6c3ae287b749db72;3c172bde8a1686d6;36c2809bd3bfd694' .. etc etc

    tixcli --stop 36c2809bd3bfd694;23ab19279dc880a8
        | Stops all (two in this case) transfers with the given IDs.

    tixcli --add <magnet_link>
        | Starts a new transfer using the given magnet link.

Notes
    The script searched for a config file named config.json within the same directory,
    where the server address, port, username, and password will be stored. If the file
    is not present, you will be prompted to enter it manually using the following syntax
        >> <username>:<password>@<ip>:<port>

    The config.json file should follow this format:

    {
        "address": "127.0.0.1",
        "port": 8888,

        "username": "username",
        "password": "password"
    }

    Do not include http:// in the address.
```

## Example Output
_The output is color coded depending on the transfer state, but is obviously not visible through GitHub._

`tixcli --list downloading:name=Nagatoro`
```
|23ab19279dc880a8: Downloading 7 (7) 0 (0) (downloading) - 69% 247 M of 355 M | 30.8 KB In/s 486B Out/s | Time Left 6:31
|===================================================================>>_______________________________
|    [EMBER] Ijiranaide Nagatoro-san - 02.mkv


|36c2809bd3bfd694: Downloading 0 (0) 0 (0) (downloading) - 32% 112 M of 341 M | 52B In/s 95B Out/s | Time Left ?:??
|==============================>>____________________________________________________________________
|    [EMBER] Ijiranaide Nagatoro-san - 04.mkv


|3c172bde8a1686d6: Downloading 5 (5) 0 (0) (downloading) - 63% 290 M of 459 M | 478 KB In/s 789B Out/s | Time Left 14:28
|=============================================================>>_____________________________________
|    [EMBER] Ijiranaide Nagatoro-san - 01.mkv


|6c3ae287b749db72: Downloading 0 (0) 0 (0) (downloading) - 34% 139 M of 398 M | 0B In/s 0B Out/s | Time Left ?:??
|================================>>__________________________________________________________________
|    [EMBER] Ijiranaide Nagatoro-san - 03.mkv
```
