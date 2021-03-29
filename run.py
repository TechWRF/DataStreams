from utils.gui import Window
from PyQt5.QtWidgets import QApplication
import sys
import multiprocessing as mp
from utils.data_streams import DataStreams
from time import sleep
from utils.working_funcs import (
    initialize_dicts,
    prepare_workspace,
    read_config,
    streaming_func,
)

# https://gist.github.com/PayseraGithub/8b41107fbf2724a5229a8710486aac2a

def processing_func(label_dict, controller_dict):    
    data_streams = DataStreams(label_dict, controller_dict)
    if controller_dict['stream']:
        data_streams.process_stream_data()
    else:
        data_streams.process_static_data()
    
    sleep(2)
    controller_dict['app_initialized'] = False
    controller_dict['app_running'] = False

if __name__ == '__main__':
    mngr = mp.Manager()
    label_dict, controller_dict = initialize_dicts(mngr)
    controller_dict = read_config(controller_dict)
    controller_dict = prepare_workspace(controller_dict)
    
    p_streaming = mp.Process(target=streaming_func, args=(controller_dict,))
    p_processing = mp.Process(target=processing_func, args=(label_dict, controller_dict))
    if controller_dict['stream']:
        p_streaming.start()
    p_processing.start()

    app = QApplication(sys.argv)
    window = Window(app, label_dict, controller_dict)
    window.show()
    app.exec_()