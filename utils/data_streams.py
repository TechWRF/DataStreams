#todo: enable windows subsystem for linux download ubuntu 
import os
import json
import pandas as pd
from datetime import datetime
from time import time
import multiprocessing as mp
from time import sleep
from utils.working_funcs import (
    initialize_dicts,
    prepare_workspace,
    read_config,
    streaming_func,
    subprocess_func
)

class DataStreams(object):
    def __init__(self, label_dict, controller_dict):
        self.label_dict = label_dict
        self.controller_dict = controller_dict
        
        self.log('\n%s' %datetime.now().strftime('%d/%m/%Y %H:%M:%S'), append_log=False)
                
    def log(self, text, append_log=True):
        with open(self.controller_dict['log_f_path'], 'a') as f:
            f.write('%s\n' %text)
        
        if self.controller_dict['local_test'] is False and append_log:
            self.controller_dict['log_text'] += '%s\n' %text
        
    @staticmethod    
    def output_to_dict(output, start_idx=0):
        """
        Converts Batch of Entries from Horizontal to Vertical Python Dictionary
        from:
            {"time":"2019-05-14 12:05:52","ip":"10.0.191.219","status_code":303}
        to:
            {"time": ["2019-05-14 12:05:52", ...],
             "ip": ["10.0.191.219", ...],
             "status_code": [303, ...]}
        """
        
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
        """
        Batch of Entries are Filtered According to Criteria:
            1) Error Code 5xx;
            2) Only Weekdays.
        And Only Unique Entries Are Kept Using drop_duplicates()
        self.label_dict is Error Counter
        """
        
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
            self.label_dict[hour] += len(data[data['hour'] == hour]['ip'])

    def write_output(self, entry_dict):
        with open(self.controller_dict['json_f_path'], 'w') as f:
            json.dump(entry_dict, f)
            
    def read_output(self):
        with open(self.controller_dict['json_f_path'], 'r') as f:
            entry_dict = json.load(f)
        return entry_dict        
    
    def finalize_static_processing(self, entry_dict):
        self.process_data(entry_dict)
        
        if self.controller_dict['local_test']:
            print(self.label_dict)
                    
        duration = time() - self.start_time
        if duration <= 60:
            time_unit = 'secs'
        elif duration > 60:
            duration /= 60
            time_unit = 'mins'
        else:
            duration /= 3600
            time_unit = 'hrs'
        
        self.log('Successfully Processed!\nDuration: %.2f %s' %(duration, time_unit))
        self.log('Result:\n%s' %self.label_dict, append_log=False)
        
    def process_static_data(self):
        """
        Along With finalize_static_processing() Processes Data as Static and 
        Saves the Result as JSON.
        """
        
        self.start_time = time()
        self.log('Running Script "%s" and Saving Result' %self.controller_dict['script_name'])
        if os.path.isfile(self.controller_dict['json_f_path']):
            try:
                self.log('Script "%s" Already Executed Before, Skipping to Processing' %self.controller_dict['script_name'])
                entry_dict = self.read_output()
                self.finalize_static_processing(entry_dict)
                return
            except:
                self.log('Could Not Read Saved JSON Data, Running Script')

        # Script is Ran using Python Subprocessing
        p = subprocess_func(self.controller_dict)
        
        stdout, stderr = p.communicate()
        stderr = stderr.decode().rstrip()
        if len(stderr): 
            raise RuntimeError('Error When Executing:\n%s' %stderr)
        
        # After Subprocessed is Finished, Data is Processed
        stdout = stdout.decode().rstrip().split('\n')
        entry_dict = self.output_to_dict(stdout)
        self.write_output(entry_dict)
        
        self.finalize_static_processing(entry_dict)
                
    def wait_for_process_startup(self):
        """
        Waits Until First Entries from Stream are Saved in .txt File Under 'streams'.
        Waits Until GUI is Loaded on Screen.
        """
        
        self.log('Waiting for Streaming to Start')
        n_entries = 0
        while n_entries == 0:
            with open(self.controller_dict['stream_f_path']) as f: 
                n_entries = len(f.read().split('\n')) - 1
            sleep(1)
        
        c = 0
        while self.controller_dict['app_running'] is False and \
        self.controller_dict['local_test'] is False:
            if c == 0:
                self.log('Waiting for GUI Startup')
                c = 1
            sleep(1)
        self.log('Streaming Started')
            
    def process_stream_data(self):
        """
        Reads Data from .txt Under 'streams' and Sends Batches to 
        Processing Functions output_to_dict() and process_data().
        Only New Data is Processed to Avoid Duplicates Using Updating
        .txt Row Index 'start_idx'.
        """
        
        self.wait_for_process_startup()
        
        start_idx, last_loop = 0, False
        while self.controller_dict['streaming_stopped'] is False:        
            self.start_time = time()
            with open(self.controller_dict['stream_f_path']) as f: 
                streamed_data = f.read().rstrip().split('\n')

            entry_dict = self.output_to_dict(streamed_data, start_idx=start_idx)
            start_idx += len(entry_dict['ip'])
            
            if self.controller_dict['local_test']:
                print(start_idx)
            
            self.process_data(entry_dict)
    
            self.do_sleep()
            
            if self.controller_dict['streaming_stopped'] and last_loop is True:
                break
            elif self.controller_dict['streaming_stopped'] and last_loop is False:
                last_loop = True
                                
    def do_sleep(self):
        sleep(max([0, self.controller_dict['sleep_time'] - (time() - self.start_time)]))
        
if __name__ == '__main__':
    mngr = mp.Manager()
    label_dict, controller_dict = initialize_dicts(mngr)
    controller_dict = read_config(controller_dict)
    controller_dict = prepare_workspace(controller_dict)
    
    controller_dict['local_test'] = True
        
    data_streams = DataStreams(label_dict, controller_dict)
    
    if controller_dict['stream']:
        p = mp.Process(target=streaming_func, args=(controller_dict, ))
        p.start()
        data_streams.process_stream_data()
    else:
        data_streams.process_static_data()