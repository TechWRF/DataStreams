# DataStreams

Streams artificial HTTP response status from .sh scripts and counts number of ip-unique hourly errors codes. Needs python 3.x to run.

There are two run modes of DataStreams:
1) Streaming of HTTP responses and processing data in parallel, can be used for large streams
2) First saving stream output and then processing data, can be used for specific list of HTTP responses

# Setup

Should work on Windows and Linux systems.

To run on Windows:
1) Clone repository
2) Download Notepad++ if you don't have it https://notepad-plus-plus.org/downloads/
3) Go to 'scripts' directory > open all scripts with Notepad++ > for each script go to 'Edit' in toolbar > EOL conversion > Unix (LF)
4) Enable Windows Subsystem for Linux. Go to Control Panel > Programs > Programs and Features > Turn Windows Features on or off > 
Scroll Down > Enable Windows Subsystem for Linux > Choose 'restart now' when prompted, Windows will download the subsystem as OS update.
5) Download Ubuntu. Go to Microsoft Store > Search 'Ubuntu' > Download it

For Linux everything should work right off the bat, however I can't testify. Try it.
Maybe you will need to grant executable permission to the scripts with <br>
*chmod +x script.sh*

If you want, you can run in virtual environment:
1) Open Command Prompt or Terminal
2) Navigate to DataStreams project directory, where you pulled it
3) *python -m venv env*
4) *env\Scripts\activate* or *./env/Scripts/activate*
5) *pip install -r requirements.txt*

You are set to go!

# Execution

Run DataStreams using:

*python run.py*

A window will pop-up, press 'START' to run first test. Soon enough, you will see the result for first 1000 iterations of Script 1 provided in task (Using 'script_test.sh').<br> 
Press 'STOP' and 'X' button to close (Do it all the time when work is finished! Don't do 'START', 'STOP', 'START', etc).<br>
Now run it again, press 'START' and the process should be faster because HTTP responses, generated in first test, will be used in processing right away. <br>
This was static mode. Let's try streaming mode now. Run DataStreams with 

*python run.py --mode=test_2*

If it worked correctly, you should see counts updating in real time, again 1000 iterations of Script 1 are used to generate HTTPS responses but this time data is processed
in parallel to generation process.

Getting excited? Run again with 

*python run.py --mode=script_1*

and 

*python run.py --mode=script_2*

With Script 1 you should notice that all hour counts level up to 900 before at least a single one is > 900, then 1800 and so on.
Script 2 never generates an error.

If something did not work, please check terminal for error, copy it and let me know, as well if there's weird behaviour.

# How It Works

Principles of how the code works: <br>
If we want to stream HTTP responses, two processes are started - streaming and processing.<br>
Streaming starts child subprocess which executes .sh scripts, while parent process writes to file standard output of child subprocess.<br>
Processing reads the same file with standard output, converts each json string to python dict and checks for unique entries using pandas tricks.<br>
Reading and processing is done in batches of new data instead of single entries because then the old data can be discarded from memory. <br>
With artificial HTTP responses this method works fine, however with realistic data there might be issues of duplicate counts if user experienced error
on the same hour twice but those two HTTP responses went to different batches of same hour.<br>
This can be solved by saving IP's for each hour of a single day and checking batch entries against IP's for duplicates. Also, batches would be chopped into hours. <br>
There is a lot more of space for scalability - we can have functionality which saves user IPs, accurate time. <br><br>
When we wish to process small amount of HTTP responses, we can use the non-stream/static mode where only processing process is started. The child subprocess, launched
in streaming mode will now be launched as processing's child subprocess. The processing will start only after child subprocess finished.<br><br>
After processes are started, gui based monitor in launched. It has a loop which is used to update results and log every second. This loop is started and stopped by user.<br><br>
Inside the .py files you will find more information!

# Applicability

Now the most important part - how to have fun with it:<br>
DataStreams is controlled using configurations. Inside config.ini you can see that the argument '--mode' we passed to run.py is actually the keys inside configuration, only in lower case.
You can write a new HTTP response .sh script and stream it by adding new key to config.ini. Example:

[LET_IT_ROLL] <br>
script_name = my_script <br>
stream = 1 <br>
sleep_time = 5 <br>

stream is boolean (0/1) <br>
sleep_time is how long (in seconds) processing function waits before grabbing new batch.  <br>
Duration but it will stay in 1 - 30 to avoid empty batches (repetition) and huge batches (Out of Memory)  <br>
Run it with<br> 
*python run.py --mode=let_it_roll*

If you wish to use some realistic HTTP response data, create 'real_data_stream.txt' in 'scripts' directory with entries in json in such simple format:

{"time":"2019-05-06 17:24:53","ip":"10.0.186.98","status_code":202} <br>
{"time":"2019-05-06 17:24:54","ip":"10.0.121.67","status_code":301} <br>
{"time":"2019-05-06 17:25:54","ip":"10.0.121.67","status_code":500} <br>
{"time":"2019-05-06 17:26:55","ip":"10.0.121.67","status_code":500} <br>
{"time":"2019-05-07 16:59:55","ip":"10.0.121.67","status_code":502} <br>
{"time":"2019-05-07 17:00:56","ip":"10.0.247.5","status_code":503} <br>
{"time":"2019-05-11 10:24:57","ip":"10.0.182.224","status_code":502} <br>
{"time":"2019-05-11 10:24:58","ip":"10.0.117.193","status_code":401} <br>
{"time":"2019-05-12 10:24:59","ip":"10.0.52.162","status_code":500} <br>
{"time":"2020-01-01 17:24:53","ip":"10.0.186.98","status_code":502} <br>
{"time":"2020-01-01 17:24:54","ip":"10.0.121.67","status_code":301} <br>
{"time":"2020-01-01 17:25:54","ip":"10.0.121.67","status_code":500} <br>

Also, create some .sh script in 'scripts' directory. It won't be executed, so it can be an empty file with .sh extension or copy of other script.<br>
Then create new configuration:

[REAL_DATA] <br>
script_name = fake_script <br>
stream = 0 <br>
sleep_time = 0 <br>

Run it with<br>
*python run.py --mode=real_data*
