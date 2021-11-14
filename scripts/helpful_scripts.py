from brownie import network, config, accounts
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development","ganache-local","testnet"]
BLOCKCHAIN_ENVIRONMENT_FORKS = ["mainnet-fork", "mainnet-fork-dev"]

def get_account(index=None, id=None):
    print(network.show_active())
    if index is not None:
        return accounts[index]
    elif id is not None:
        return accounts.load(id)
    if network.show_active() == "development" or network.show_active() in BLOCKCHAIN_ENVIRONMENT_FORKS:
        return accounts[0]
    elif network.show_active() == "ganache-local":
        return accounts.add(config["wallets"]["from_ganache"])
    else:
        return accounts.add(config["wallets"]["from_key"])

def in_local_development():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        return True
    else:
        return False




