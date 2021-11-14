from brownie import network ,interface, MockV3Aggregator, config, Contract, VRFCoordinatorMock, MockOracle, LinkToken, Lottery
from scripts.helpful_scripts import get_account

BLOCKCHAIN_ENVIRONMENT_FORKS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development","ganache-local","testnet"]
DECIMALS = 8
STARTING_PRICE = 473484000000

def deploy_mocks():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        account = get_account()
        print("Deploying Mocks")
        if len(MockV3Aggregator)<=0:
            MockV3Aggregator.deploy(DECIMALS,STARTING_PRICE, {"from":account})
        if len(LinkToken)<=0:
            LinkToken.deploy({"from":account})
        if len(MockOracle)<=0:
            MockOracle.deploy(get_contract('vrf_link').address,{"from":account})
        if len(VRFCoordinatorMock)<=0:
            link_address = get_contract('vrf_link').address
            VRFCoordinatorMock.deploy(link_address, {"from":account})
        print("Mocks deployed")
        return 1
    else:
        return 0

# Deploy in anynet
def deploy_lottery(minimum_fee):
    deploy_mocks()
    
    price_feed_address = get_contract('eth_usd_price_feed')
    account = get_account()
    vrf_address = get_contract("vrf_coordinator").address
    vrf_keyhash = config["networks"][network.show_active()]["vrf_keyhash"]
    vrf_link = get_contract("vrf_link").address
    vrf_fee = config["networks"][network.show_active()]["vrf_fee"]
    lottery = Lottery.deploy(minimum_fee, price_feed_address, vrf_address,vrf_link,vrf_fee,vrf_keyhash,{"from": account},publish_source=config["networks"][network.show_active()].get("verify"))
    return lottery

def main():
    print("Active chain is: ", network.show_active())
    deploy_mocks()
    deploy_lottery(50)
 
contract_to_mock = { "eth_usd_price_feed": MockV3Aggregator,
                    "vrf_coordinator": VRFCoordinatorMock,
                    'vrf_oracle': MockOracle,
                    'vrf_link' : LinkToken}
 
def get_contract(contract_name):
    contract_type = contract_to_mock.get(contract_name)
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type)>0:
            contract =  contract_type[-1]
    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        if contract_name == "eth_usd_price_feed":
            contract = interface.AggregatorV3Interface(contract_address)
        if contract_name == "vrf_coordinator":
            contract = interface.VRFCoordinatorV2Interface(contract_address)
        if contract_name == "vrf_oracle":
            contract = interface.OracleInterface(contract_address)
        if contract_name == "vrf_link":
            contract = interface.LinkTokenInterface(contract_address)
        #contract = Contract.from_abi(contract_type._name, contract_address, contract_type.abi)
    return contract

def fund_with_link(contract_address, account=None, link_token=None, amount=100000000000):
    account = account if account else get_account()
    print ("Account is: ", account)
    print ("Account funds: ", account.balance())
    link_token = link_token if link_token else get_contract("vrf_link")
    #link_token_contract = interface.LinkTokenInterface(link_token)
    print ("Contract address to fund with link: ",contract_address)
    tx = link_token.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    print ("Contract address balance", link_token.balanceOf(contract_address))
    return tx
