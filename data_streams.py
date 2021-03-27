import subprocess
import os, sys
import json
import pandas as pd
from datetime import datetime
from time import time
import numpy as np
import multiprocessing
from time import sleep
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import configparser
import argparse

class DataStreams(object):
    def __init__(self, script_name, stream, sleep_time):
        self.script_name = script_name
        self.stream = stream
        self.error_counter = {hour: 0 for hour in range(0, 24)}
        self.sleep_time = sleep_time
        
    def prepare_workspace(self):
        cwd = get_cwd()
        
        scripts_dir = os.path.join(cwd, 'scripts')
        if os.path.isdir(scripts_dir) is False:
            raise RuntimeError('Scripts Directory Does Not Exist; See Documentation')
        
        script_file = '%s.sh' %self.script_name
        if script_file not in os.listdir(scripts_dir):
            raise RuntimeError('Script File "%s" Does Not Exist; See Documentation' %script_file)
         
        stream_dir = os.path.join(cwd, 'streams')
        json_dir = os.path.join(cwd, 'jsons')
        log_dir = os.path.join(cwd, 'logs')
        for direc in [stream_dir, json_dir, log_dir]:
            if os.path.isdir(direc) is False:
                os.mkdir(direc)
                
        self.stream_f_path = os.path.join(stream_dir, '%s_stream.txt' %self.script_name)
        if self.stream:
            with open(self.stream_f_path, 'w') as f: pass
        
        self.json_f_path = os.path.join(json_dir, '%s_out.json' %self.script_name)
        
        self.log_f_path = os.path.join(log_dir, '%s_log.txt' %self.script_name)
        if os.path.isfile(self.log_f_path) is False:
            with open(self.log_f_path, 'w') as f: pass
        
        self.log('\n%s' %datetime.now().strftime('%d/%m/%Y %H:%M:%S'))
        
        self.script_path = '/'.join(['scripts', '%s.sh' %self.script_name])
        return self.script_path, self.stream_f_path
    
    def log(self, text):
        with open(self.log_f_path, 'a') as f: f.write('%s\n' %text)
        
    def do_sleep(self, start_time):
        sleep(max([0, time() - start_time - self.sleep_time]))
        
    def wait_for_process_startup(self):    
        n_entries = 0
        while n_entries == 0:
            start_time = time()
            with open(self.stream_f_path) as f: 
                n_entries = len(f.read().split('\n')) - 1
            self.do_sleep(start_time)

    @staticmethod    
    def output_to_dict(output, start_idx=0):
        for i, entry in enumerate(output):
            if i >= start_idx:
                if entry.endswith('}') is False:
                    return vertical_entry_dict
                
                entry_dict = json.loads(entry)
                if i - start_idx == 0:
                    keys = list(entry_dict.keys())
                    vertical_entry_dict = {k: [] for k in keys}
                else:
                    for k in keys:
                        vertical_entry_dict[k].append(entry_dict[k])
        return vertical_entry_dict

    def process_data(self, entry_dict):
        data = pd.DataFrame(entry_dict)
        data['time'] = pd.to_datetime(data['time'])        
        data['date'] = data['time'].dt.floor('d')
        data['hour'] = data['time'].dt.hour
        data['weekday'] = data['time'].dt.weekday
        data = data[data['status_code'] >= 500]
        data = data[data['status_code'] < 600]
        data = data[data['weekday'] < 5]
        data = data.drop(['time', 'weekday', 'status_code'], axis=1).drop_duplicates()
        
        for hour in range(0, 24):
            self.error_counter[hour] += len(data[data['hour'] == hour]['ip'])

    def read_output(self):
        with open(self.json_f_path, 'r') as f:
            entry_dict = json.load(f)
        return entry_dict

    def plot_result(self):
        plt.bar(list(self.error_counter.keys()), list(self.error_counter.values()))
        plt.show()

    def single_shot(self):
        if os.path.isfile(self.json_f_path):
            try:
                with open(self.json_f_path, 'r') as f: 
                    entry_dict = self.read_output()
                self.log('Script "%s" Already Executed Before, Returning' %self.script_name)
                return entry_dict
            except: pass   
            
        self.log('Running Script "%s" and Dumping Result' %self.script_name)
        
        start_time = time()
        p = subprocess.Popen(['bash', self.script_path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = p.communicate()
        stderr = stderr.decode().rstrip()
        if len(stderr): 
            raise RuntimeError('Error When Executing:\n%s' %stderr)
        
        stdout = stdout.decode().rstrip().split('\n')
        entry_dict = self.output_to_dict(stdout)
        with open(self.json_f_path, 'w') as f:
            json.dump(entry_dict, f)
        
        entry_dict = self.read_output()
        
        duration = time() - start_time
        if duration <= 60:
            time_unit = 'secs'
        elif duration > 60:
            duration /= 60
            time_unit = 'mins'
        else:
            duration /= 3600
            time_unit = 'hrs'
        self.log('Successfully Executed!\nDuration: %.2f %s' %(duration, time_unit))
        return entry_dict
    
    def process_static_data(self):
        entry_dict = self.single_shot()
        self.process_data(entry_dict)
        self.plot_result()

    def process_stream_data(self, p):
        self.wait_for_process_startup()
        
        start_idx, last_loop = 0, False
        while True:
            start_time = time()
            with open(self.stream_f_path) as f: 
                streamed_data = f.read().rstrip().split('\n')
                
            n_entries = len(streamed_data) - 1
            if n_entries == start_idx and n_entries > 1:
                break
    
            entry_dict = self.output_to_dict(streamed_data, start_idx=start_idx)
            start_idx += len(entry_dict['ip'])
            print(start_idx)
            
            self.process_data(entry_dict)
            self.plot_result()
    
            self.do_sleep(start_time)
            
            if p.is_alive() is False and last_loop is True:
                break
            elif p.is_alive() is False and last_loop is False:
                last_loop = True

def get_cwd():
    py_path = os.path.realpath(__file__)
    return os.path.split(py_path)[0]

def read_config(run_mode):
    cwd = get_cwd()
    config = configparser.ConfigParser()
    config_path = os.path.join(cwd, 'config.ini')
    config.read(config_path)

    script_name = config[run_mode]['script_name']
    stream = config.getboolean(run_mode, 'stream')
    sleep_time = float(config[run_mode]['sleep_time'])
    return script_name, stream, sleep_time

def get_run_mode():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', help='Which Config to Use', default='test_1')
    args = parser.parse_args()
    return args.mode.upper()
    
def streaming_func(script_path, stream_f_path):
    with open(stream_f_path, 'wb') as f:
        sub_p = subprocess.Popen(['bash', script_path], shell=True, stdout=subprocess.PIPE)
        for c in iter(lambda: sub_p.stdout.read(1), b''): 
            f.write(c)
                
if __name__ == '__main__':
    run_mode = get_run_mode()
    script_name, stream, sleep_time = read_config(run_mode)
    
    data_streams = DataStreams(script_name, stream, sleep_time)
    script_path, stream_f_path = data_streams.prepare_workspace()
    if stream:
        p = multiprocessing.Process(target=streaming_func, args=(script_path, stream_f_path))
        p.start()
        data_streams.process_stream_data(p)
    else:
        data_streams.process_static_data()
        
# https://gist.github.com/PayseraGithub/8b41107fbf2724a5229a8710486aac2a