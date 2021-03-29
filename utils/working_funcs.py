import os
import configparser
import argparse
import subprocess
from time import sleep

def get_cwd():
    py_path = os.path.realpath(__file__)
    py_path_split = py_path.split(os.sep)
    if 'utils' == py_path_split[-2]:
        cwd = os.sep.join(py_path_split[:-2])
    else:
        cwd = os.sep.join(py_path_split[:-1])
    return cwd

def prepare_workspace(controller_dict):
    """
    Inspects Legitimacy of Working Directory and Creates Directories for
    Streams, Logs, JSONs Containing Results Incase of Static Processing.
    """
    
    cwd = get_cwd()
    
    scripts_dir = os.path.join(cwd, 'scripts')
    if os.path.isdir(scripts_dir) is False:
        raise RuntimeError('Scripts Directory Does Not Exist; See Documentation')
    
    script_file = '%s.sh' %controller_dict['script_name']
    if script_file not in os.listdir(scripts_dir):
        raise RuntimeError('Script File "%s" Does Not Exist; See Documentation' %script_file)
     
    stream_dir = os.path.join(cwd, 'streams')
    json_dir = os.path.join(cwd, 'jsons')
    log_dir = os.path.join(cwd, 'logs')
    for direc in [stream_dir, json_dir, log_dir]:
        if os.path.isdir(direc) is False:
            os.mkdir(direc)
            
    stream_f_path = os.path.join(stream_dir, '%s_stream.txt' %controller_dict['script_name'])
    if controller_dict['stream']:
        with open(stream_f_path, 'w') as f: pass
    
    json_f_path = os.path.join(json_dir, '%s_out.json' %controller_dict['script_name'])
    
    log_f_path = os.path.join(log_dir, '%s_log.txt' %controller_dict['script_name'])
    if os.path.isfile(log_f_path) is False:
        with open(log_f_path, 'w') as f: pass

    script_path = '/'.join(['scripts', '%s.sh' %controller_dict['script_name']])
    
    controller_dict['script_path'] = script_path
    controller_dict['stream_f_path'] = stream_f_path
    controller_dict['json_f_path'] = json_f_path
    controller_dict['log_f_path'] = log_f_path
    controller_dict['cwd'] = cwd
    return controller_dict

def initialize_dicts(mngr):
    """
    label_dict is Error Counter
    controller_dict is Placeholder for Paths, Bools and Log Text. 
    """
    
    label_dict = mngr.dict()
    for h in range(24):
        label_dict[h] = 0
        
    controller_dict = mngr.dict()
    controller_dict['app_initialized'] = True
    controller_dict['app_running'] = False
    controller_dict['log_text'] = ''
    controller_dict['local_test'] = False
    controller_dict['streaming_stopped'] = False
    return label_dict, controller_dict

def get_run_mode():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', help='Which Config to Use', default='test_1')
    args = parser.parse_args()
    return args.mode.upper()

def read_config(controller_dict):
    cwd = get_cwd()
    config = configparser.ConfigParser()
    config_path = os.path.join(cwd, 'config.ini')
    config.read(config_path)
    
    run_mode = get_run_mode()
    controller_dict['script_name'] = config[run_mode]['script_name']
    controller_dict['stream'] = config.getboolean(run_mode, 'stream')
    controller_dict['sleep_time'] = float(config[run_mode]['sleep_time'])
    return controller_dict

def subprocess_func(controller_dict):
    """
    Starts Subprocess for Static or Stream Processing.
    """
    
    p = subprocess.Popen(['bash', '%s.sh' %controller_dict['script_name']],
                        shell=True, 
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        cwd=os.path.join(controller_dict['cwd'], 'scripts'))
    
    return p

def streaming_func(controller_dict):
    """
    Writes Streamed Output to .txt under 'streams'
    'if' Inside is Needed to Terminate Subprocess When App is Terminated.
    It Is Not an Expensive Method - Duration Increases by 2.1 % 
    (Tested With 1000 Iterations/Rows).
    """
    
    with open(controller_dict['stream_f_path'], 'wb') as f:
        sub_p = subprocess_func(controller_dict)
        
        for c in iter(lambda: sub_p.stdout.read(1), b''): 
            f.write(c)
            if controller_dict['app_initialized'] is False: 
                controller_dict['streaming_stopped'] = True
                break
                
    sub_p.kill()
    sub_p.terminate()
    controller_dict['log_text'] += 'Streaming Terminated'
    
    sleep(2)
    controller_dict['app_initialized'] = False
    controller_dict['app_running'] = False