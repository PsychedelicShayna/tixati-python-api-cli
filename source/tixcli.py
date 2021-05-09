from ctypes import windll, Structure, c_short, c_ushort, byref
from tixati_api import TixatiServer
import sys, os

if windll:
    class _COORD(Structure):
        _fields_ = [("X", c_short),
                    ("Y", c_short)]

    class _SMALL_RECT(Structure):
        _fields_ = [("Left", c_short),
                    ("Top", c_short),
                    ("Right", c_short),
                    ("Bottom", c_short)]

    class _CONSOLE_SCREEN_BUFFER_INFO(Structure):
        _fields_ = [("dwSize", _COORD),
                    ("dwCursorPosition", _COORD),
                    ("wAttributes", c_ushort),
                    ("srWindow", _SMALL_RECT),
                    ("dwMaximumWindowSize", _COORD)]

    STD_INPUT_HANDLE = -10
    STD_OUTPUT_HANDLE= -11
    STD_ERROR_HANDLE = -12

    FOREGROUND_BLUE = 0x01 # text color contains blue.
    FOREGROUND_GREEN= 0x02 # text color contains green.
    FOREGROUND_RED  = 0x04 # text color contains red.
    FOREGROUND_INTENSITY = 0x08 # text color is intensified.
    BACKGROUND_BLUE = 0x10 # background color contains blue.
    BACKGROUND_GREEN= 0x20 # background color contains green.
    BACKGROUND_RED  = 0x40 # background color contains red.
    BACKGROUND_INTENSITY = 0x80 # background color is intensified.

    std_out_handle = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)

    def SetConsoleColor(color, handle=std_out_handle):
        return windll.kernel32.SetConsoleTextAttribute(handle, color)

    def GetConsoleColor(handle=std_out_handle):
        csbi = _CONSOLE_SCREEN_BUFFER_INFO()
        result = windll.kernel32.GetConsoleScreenBufferInfo(handle, byref(csbi))
        if not result:
            return FOREGROUND_RED | FOREGROUND_INTENSITY
        else:
            return csbi.wAttributes
else:
    def SetConsoleColor(color):
        # Cross-platform Implementation Todo
        pass

    def GetConsoleColor():
        # Cross-platform Implementation Todo
        pass

DEFAULT_CONFIG_PATH:str = "{0}/config.json".format(os.path.dirname(__file__))

def RenderTransferList(server_instance:TixatiServer, list_filters:str) -> str:
    rendered_lines:list = []

    transfers = server_instance.FetchTransfers()

    name_filter = None
    status_filters = []
    id_print_mode = False

    if list_filters != "all":
        split_filters = list_filters.split(":")

        for lfilter in split_filters:
            if "=" in lfilter:
                split_lfilter = lfilter.split("=")

                if len(split_lfilter) == 2 and split_lfilter[0] == "name":
                    name_filter = split_lfilter[1]

            elif lfilter in ('complete', 'seeding', 'downloading', 'offline'):
                status_filters.append(lfilter)

            elif lfilter == "id":
                id_print_mode = True

    if name_filter:
        transfers = list(filter(lambda transfer: name_filter.lower() in transfer.Title.lower(), transfers))

    if len(status_filters) > 0:
        transfers = list(filter(lambda transfer: transfer.StatusClass in status_filters, transfers))

    if id_print_mode:
        print(";".join([transfer.Id for transfer in transfers]), end="")
    else:
        for transfer in transfers:
            original_color = GetConsoleColor()

            if transfer.StatusClass.lower() == "complete":
                SetConsoleColor(FOREGROUND_RED | FOREGROUND_INTENSITY)
            elif transfer.StatusClass.lower() == "seeding":
                SetConsoleColor(FOREGROUND_BLUE | FOREGROUND_GREEN | FOREGROUND_INTENSITY)
            elif transfer.StatusClass.lower() == "offline":
                SetConsoleColor(FOREGROUND_GREEN | FOREGROUND_RED | FOREGROUND_INTENSITY)
            else:
                SetConsoleColor(FOREGROUND_GREEN | FOREGROUND_INTENSITY)


            print("|{tid}: {status} ({cstatus}) - {percent}% {size} | {byin}B In/s {byout}B Out/s | Time Left {time}".format(
                tid = transfer.Id, cstatus=transfer.StatusClass, status=transfer.Status, percent=transfer.Percent, size=transfer.SizeLeft,
                byin = transfer.BytesIn, byout=transfer.BytesOut, time=transfer.TimeLeft
            ))

            progress_line = (("=" * (int(transfer.Percent)-2) ) + ">>") + ("_" * (100 - int(transfer.Percent)))

            print("|" + progress_line)
            print("|    " + transfer.Title + "\n\n")

            SetConsoleColor(original_color)

HELP_TEXT = """
General Operations
   --help (-h)                                | This help text.

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
    --check  (-c) <id;id;id..>                | Checks the presence of the transfer's files, re-initiates the transfer if missing.

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
        "address": "http://127.0.0.1",
        "port": 8888,

        "username": "username",
        "password": "password"
    }
"""

if __name__ == "__main__":
    config:str = None

    if os.path.isfile(DEFAULT_CONFIG_PATH):
        config = DEFAULT_CONFIG_PATH
    else:
        print("Config file not found, please supply the server configuration manually.")
        config_str:str = input("(<username>:<password>@<ip>:<port>) >> ")

        try:
            config = {
                "username": config_str.split("@")[0].split(":")[0],
                "password": config_str.split("@")[0].split(":")[1],

                "address": config_str.split("@")[1].split(":")[0],
                "port": int(config_str.split("@")[1].split(":")[1])
            }
        except IndexError as exception:
            print("\nIndexError exception, invalid configuration format.")
            print("Format should be: <username>:<password>@<ip>:<port>\n\nException %s" % ("-" * 30))
            raise exception

        except ValueError as exception:
            print("\nValueError exception, port value probably not numeric.\n\nException %s" % ("-" * 30))
            raise exception

    try:
        server = TixatiServer(config = config)
    except Exception as exception:
        print("Failed to create a TixatiServer instance due to an exception.\n\nException %s" % ("-" * 30))
        raise exception

    if len(sys.argv) > 1:
        operations:list = []

        for index, argument in enumerate(sys.argv):
            next_argument = sys.argv[index + 1] if (index + 1) < len(sys.argv) else None

            if argument in ["--help", "-h"]:
                print(HELP_TEXT)
                raise SystemExit()

            # Operations that rely on follow-up arguments.
            if next_argument:
                if argument in ["--list", "-l"]:
                    operations.append(("list", next_argument))

                elif argument in ["--add", '-a']:
                    # Next argument should be a magnet link.
                    operations.append(('add', next_argument))

                elif argument in ["--remove", "-r"]:
                    # Next argument should be transfer ID.
                    operations.append(("remove", next_argument))

                elif argument in ["--delete", "-d"]:
                    # Next argument should be transfer ID.
                    operations.append(("delete", next_argument))

                elif argument in ["--start", "-st"]:
                    # Next argument should be transfer ID.
                    operations.append(("start", next_argument))

                elif argument in ["--stop", "-sp"]:
                    # Next argument should be transfer ID.
                    operations.append(("stop", next_argument))

                elif argument in ["--check", "-c"]:
                    # Next argument should be transfer ID.
                    operations.append(("check", next_argument))

        for operation in operations:
            operation_func_map:dict = {
                "list":   lambda list_filter: RenderTransferList(server, list_filter),

                "add":    server.AddTransfer,
                "remove": server.RemoveTransfer,
                "delete": server.DeleteTransfer,
                "stop":   server.StopTransfer,
                "start":  server.StartTransfer,
                "check":  server.CheckFiles
            }

            if operation[0] in operation_func_map:
                if len(operation) > 1:
                    if ";" in operation[1]:
                        args = operation[1].split(";")

                        for arg in args:
                            operation_func_map[operation[0]](arg)
                    else:
                        operation_func_map[operation[0]](operation[1])
                else:
                    operation_func_map[operation[0]]()
    else:
        # Interactive Mode Todo
        print(HELP_TEXT)
