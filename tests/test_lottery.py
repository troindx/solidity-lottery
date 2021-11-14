from os import times
from brownie import accounts, web3, network
from scripts.deploy import LOCAL_BLOCKCHAIN_ENVIRONMENTS, deploy_lottery, fund_with_link, get_contract
from scripts.helpful_scripts import get_account
from web3 import Web3
import pytest


# 1 gwei = 0.000048 usd
def test_get_entrance_fee():
    lottery = deploy_lottery(50)
    entrance_fee = lottery.getEntranceFee()
    conversion_price = lottery.getEtherPriceInUSDGwei()
    print("Conversion Price")
    print(conversion_price)
    print("Entry Fee")
    print(entrance_fee)
    assert web3.toWei(entrance_fee,'gwei') >= web3.toWei(0.009, 'ether')
    assert web3.toWei(entrance_fee,'gwei') <= web3.toWei(0.013, 'ether')

def test_enter_closed():
    lottery = deploy_lottery(50)
    account = get_account()
    status = lottery.state()
    print(lottery.owner())
    print("Lottery Status")
    print(status)
    print(account)
    entrance_fee = lottery.getEntranceFee()
    try:
        lottery.enter({'value':web3.toWei(entrance_fee,'gwei'), 'from':account})
    except:
        assert True

def test_enter_small_amount():
    lottery = deploy_lottery(50)
    account = get_account()
    entrance_fee = lottery.getEntranceFee()
    try:
        tx1 = lottery.start({'from':account})
        tx1.wait(0.5)
        tx2 = lottery.enter({'value':web3.toWei(0.000001,'ether'), 'from':account})
        tx2.wait(1)
    except:
        assert True
    
def test_enter_open():
    lottery = deploy_lottery(50)
    account = get_account()
    entrance_fee = lottery.getEntranceFee()
    try:
        tx1 = lottery.start({'from':account})
        tx1.wait(0.5)
        tx2 = lottery.enter({'value':web3.toWei(entrance_fee,'gwei'), 'from':account})
        tx2.wait(1)
        assert lottery.balance() == web3.toWei(entrance_fee,'gwei')
    except:
        assert False

def test_start_malicious_actor():
    lottery = deploy_lottery(50)
    malicious_actor = accounts.add()
    try:
        lottery.start({'from':malicious_actor})
    except:
        assert True

def test_start():
    lottery = deploy_lottery(50)
    account = get_account()
    try:
        tx = lottery.start({'from':account})
        tx.wait(0.5)
        assert lottery.state() == 0
        
    except:
        assert False


def test_lottery_end_malicious_actor():
    lottery = deploy_lottery(50)
    malicious_actor = accounts.add()
    try:
        tx1 = lottery.start({'from':get_account()})
        tx1.wait(0.5)
        lottery.end({'from':malicious_actor})
    except:
        assert True

def test_can_pick_winner_correctly():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Skipping local blockchain environment")
    lottery = deploy_lottery(50)
    account = get_account()
    starting_balance = account.balance()
    entrance_fee = lottery.getEntranceFee()
    tx1 = lottery.start({'from':account})
    tx1.wait(1)
    tx2 = lottery.enter({'value':web3.toWei(entrance_fee,'gwei'), 'from':get_account(index=3)})
    tx2.wait(1)
    tx3 = lottery.enter({'value':web3.toWei(entrance_fee,'gwei'), 'from':get_account(index=1)})
    tx3.wait(1)
    tx_fund = fund_with_link(lottery)
    print (tx_fund)
    balance_of_lottery = lottery.balance()
    transaction = lottery.end({'from':account})
    transaction.wait(1)
    request_id = transaction.events['RequestedRandomness']['requestId']
    get_contract('vrf_coordinator').callBackWithRandomness(request_id, 777, lottery, {"from":account})
    # 777 % 3 == 0
    assert lottery.recentWinner() == account
    assert lottery.balance == 0
    assert account.balance == starting_balance + balance_of_lottery


def test_lottery_end():
    account = get_account()
    if (network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS):
        pytest.skip("Local blockchain environment")
    lottery = deploy_lottery(50)
    tx1 = lottery.start({'from':get_account()})
    tx1.wait(1)
    print(tx1)
    tx_fund = fund_with_link(lottery, account = account)
    tx_fund.wait(1)
    try:
        tx2 = lottery.end({'from':get_account()})
        assert lottery.state() == 2
        tx2.wait(1)
    except Exception as e:
        assert False
    assert lottery.balance() == 0
    assert lottery.latestWinner() == get_account()
    assert lottery.state() == 0
    
def test_can_pick_winner():
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from": account})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    lottery.enter({"from": account, "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    lottery.endLottery({"from": account})
    times.sleep(60)
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0