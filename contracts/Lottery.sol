//SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";

contract Lottery is VRFConsumerBase,Ownable{
    address[] public players;
    address public recentWinner;
    uint256 public randomness;
    uint256 public minimum_fee;
    event RequestedRandomness(bytes32 requestId);
    address public vrfCoordinator; 
    address public link;
    enum lottery_state{
        open,
        closed,
        calculating_prizes
    }
    lottery_state public state;

    uint256 public fee;
    bytes32 public keyhash;
    AggregatorV3Interface internal ethUSDPriceFeed;
    constructor(uint256 _minimum_fee_in_usd, 
                address _price_feed_address, 
                address _vrfCoordinator, 
                address _link,
                uint256 _fee,
                bytes32 _keyhash) VRFConsumerBase(_vrfCoordinator, _link)
    {
        require(_minimum_fee_in_usd > 0, "Minimum fee must be greater than 0");
        state = lottery_state.closed;
        minimum_fee = _minimum_fee_in_usd;
        ethUSDPriceFeed = AggregatorV3Interface(_price_feed_address);
        fee = _fee;
        players = new address[](0);
        keyhash = _keyhash;
        vrfCoordinator = _vrfCoordinator;
        link = _link;
    }
    function enter() public payable{
        //50 USD minimum 
        require(state == lottery_state.open, "Lottery is not open");
        uint256 minimum_fee_in_gwei = getEntranceFee();
        require(msg.value >= minimum_fee_in_gwei, "You must pay at least 50 USD");
        players.push(msg.sender);
    }
    function getEntranceFee() public view returns (uint256){
        // 1 gwei = 0.000048 usd
        // 1 USD = 0,00021 Ethereum
        // 1 USD = 2100000000
        uint256 price = getEtherPriceInUSDGwei();
        uint256 costToEnter = (minimum_fee * 10**17) / price;
        return costToEnter; //In dollars * gwei
    }

    function getEtherPriceInUSDGwei() public view returns (uint256){
        // 1 gwei = 0.000048 usd
        // 1 USD = 0,00021 Ethereum
        // 1 USD = 2100000000
        (,int256 preadjusted_price,,,) = ethUSDPriceFeed.latestRoundData();
        uint256 price = uint256(preadjusted_price);
        return price;
    }

    function start() onlyOwner public {
        require(state == lottery_state.closed, "Lottery is already open");
        state = lottery_state.open;
    }
    
    function end() onlyOwner public  {
        require(state == lottery_state.open, "Lottery is not open");
        state = lottery_state.calculating_prizes;
        bytes32 requestId = requestRandomness(keyhash,fee);
        emit RequestedRandomness(requestId);
    }

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness) internal override{
        require(state == lottery_state.calculating_prizes,"Not there yet");
        require(randomness > 0,"Randomness cannot be 0");
        uint256 indexOfWinner = randomness % players.length;
        recentWinner = players[indexOfWinner];
        payable(recentWinner).transfer(address(this).balance);
        randomness = _randomness;

        //reset
        players = new address[](0);
        state = lottery_state.closed;
    }

    function toggleState() onlyOwner public {
        if(state == lottery_state.open){
            end();
        } else if(state == lottery_state.closed){
            start();
        }
    }
}