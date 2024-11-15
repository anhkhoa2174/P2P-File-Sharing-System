import argparse
import mmap

def submit_info(args):
    #TODO: issue the submit command procedure
    with open(filepath, mode="r+", encoding="utf-8") as file_obj:
        file_obj.truncate(100)
        with mmap.mmap(file_obj.fileno(), length=0, access=mmap.ACCESS_WRITE, offset=0) as map_obj:
            text = f"submit_info"
            print(text)
            map_obj.write(text.encode("utf-8"))

def get_list(args):
    #TODO: issue the get_list command procedure
    with open(filepath, mode="r+", encoding="utf-8") as file_obj:
        file_obj.truncate(100)
        with mmap.mmap(file_obj.fileno(), length=0, access=mmap.ACCESS_WRITE, offset=0) as map_obj:
            text = f"getlist"
            map_obj.write(text.encode("utf-8"))

#TODO: implement all the command procedure

class NodeCLI:
    def __init__(self):
        self.parser = argparse.ArgumentParser(prog='NodeCLI', description='CLI for interacting with Node')
        self.add_subparsers()

    def add_subparsers(self):
        self.parser.add_argument('--func')
        self.parser.add_argument('--server-ip')
        self.parser.add_argument('--server-port', type=int)
        self.parser.add_argument('--agent-path')

    def run(self):
        args = self.parser.parse_args()
        f = globals()[args.func]
        f(args)

def main():
    cli = NodeCLI()
    cli.run()

if __name__ == "__main__":
    main()