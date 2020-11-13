from client import Client


def main():
  client = Client()
  client.setup_batfish()
  client.load_snapshot("/home/leo/repos/verifier/configs/origin", "origin")
  client.load_snapshot("/home/leo/repos/verifier/configs/update1", "update1")
  client.check_traffic("origin", "update1")


if __name__ == "__main__":
  main()