<h1>ASICseer Pool Monitor With Live Share Activity</h1>

Monitors the activity of ASICseer Pool by parsing and displaying advanced operational/status data. In this version you can see the difficulty level of each share that was submitted to the pool. It gets the share activity data from the level 6 log file. The pool has to be started with the "-l 6" log level indicator at the end of the start command.<br><br>

<img width="696" height="426" alt="asicseerpoolmonitorv218" src="https://github.com/user-attachments/assets/1dbf034d-79ac-442c-9b9c-3a9a60fabd4f" />


<h2>What are the current features?</h2>

<h3>NETWORK section:</h3>
<b>Difficulty =</b> network difficulty.<br>
<b>Block Hash =</b> a digital fingerprint or unique identifier of the last block.<br>
<b>Current Reward =</b> current reward paid out when block has been solved.<br><br>

<h3>SESSION section:</h3>
<b>Runtime =</b> displays how long the pool has been continuously operating, the number of users and workers pointed to the pool.<br><br>

<h3>USER section:</h3>
<b>Worker / IP / Username =</b> username configured in miner / IP address of the miner / worker name assigned for the miner.<br><br>

<h3>HASHRATE section:</h3>
<b>Performance =</b> total hashrate the pool is receiving from miner(s).<br><br>

<h3>SHARES section:</h3>
<b>Status =</b> number of total accepted and rejected shares submitted to the pool. Rejection rate in percentage.<br>
<b>SPS =</b> number of total shares per second submitted to the pool.<br>
<b>Effort =</b> the amount of work your miners have put in relative to the statistical average to solve a block.<br><br>

<h3>BLOCKS section:</h3>
<b>Accepted =</b> number of total blocks that have been found.<br>
<b>Last Block Found =</b> date and timestamp the last block was found.<br>
<b>Block Height =</b> the block height when the block was solved.<br>
<b>Winner Worker =</b> the identity of the worker that solved the block.<br>
<b>Solved Effort =</b> the percentage of the effort when the block was solved.<br>
<b>Solved Share Difficulty =</b> the share difficulty the worker submitted.<br><br>

<h3>Share Activity section:</h3>
<b>Time, Worker, Difficulty =</b> displays the real time share submission activity (It shows the difficulty level of every single share that was submitted to the pool).<br><br>

<h2>What are the upcoming features?</h2>
I am open to feedback and future requests to enhance the capability of this application. Please do not hesitate to write up an issue if you notice anything not working properly. Alternatively, you can reach out via Reddit: https://www.reddit.com/r/Options4Good/<br><br>

<h2>Installation, Configuration & Start</h2>
<b>Linux Dependencies</b><br><br>
In the terminal perform the below command:<br><br>

```bash
sudo apt update && sudo apt install python3 python3-pip python3-venv -y
```

Download the latest asicseerpoolmonitorv2.py file from the "Releases" section: https://github.com/options4good/ASICseer-Pool-Monitor-With-Live-Share-Activity/releases<br><br>

Start the application from the terminal running the below command:

```bash
python3 asicseerpoolmonitorv2.py
```

<br>

<h4>Donations are highly appreciated and can be made via crypto:</h4>
<b>DGB</b> wallet address:&nbsp;&nbsp;DEkZrJo1BHdiqnQq1XQSWGymEcDWGAWwZs<br>
<b>DOGE</b> wallet address:&nbsp;&nbsp;DKZ9sv4VoTiQQdwi7VY25573UfpQqZJfYf<br>
<b>LTC</b> wallet address:&nbsp;&nbsp;MJw3XHpR65Ec8rKEBthK5Dnvcy1CixYGTa<br>
<b>BCH</b> wallet address:&nbsp;&nbsp;bitcoincash:qq66dg3vhczrqf4zy4kxje3c45vz47khsufsludxcc<br><br>
Thank you.
<br><br>
