# import time
from abc import ABCMeta
from threading import Lock, Thread, Event
import socket
# import struct
import warnings
# import numpy as np
from numpy import round, asarray, array, zeros, empty, arange, mod, hstack
from struct import pack,unpack
from time import perf_counter, sleep


warnings.filterwarnings('ignore')  # or warnings.filterwarnings("default")

def _unpack_header(header_packet):
        # header for a packet
        chan_name = unpack('>4s', header_packet[:4])
        w_code = unpack('>H', header_packet[4:6])
        w_request = unpack('>H', header_packet[6:8])
        packet_size = unpack('>I', header_packet[8:])

        return (chan_name[0].decode('utf-8','ignore'), w_code[0], w_request[0], packet_size[0])

class dataserver_thread(Thread, metaclass=ABCMeta):
    '''
    Read data from EEG device in real time.
    Actually, there is a data buffer that caches data from the EEG device all the time.
    '''
    """
    CHANNELS = [
        'FP1', 'FPZ', 'FP2', 'AF3', 'AF4', 'F7', 'F5', 'F3',
        'F1', 'FZ', 'F2', 'F4', 'F6', 'F8', 'FT7', 'FC5',
        'FC3', 'FC1', 'FCZ', 'FC2', 'FC4', 'FC6', 'FT8', 'T7',
        'C5', 'C3', 'C1', 'CZ', 'C2', 'C4', 'C6', 'T8',
        'M1', 'TP7', 'CP5', 'CP3', 'CP1', 'CPZ', 'CP2', 'CP4',
        'CP6', 'TP8', 'M2', 'P7', 'P5', 'P3', 'P1', 'PZ',
        'P2', 'P4', 'P6', 'P8', 'PO7', 'PO5', 'PO3', 'POZ',
        'PO4', 'PO6', 'PO8', 'CB1', 'O1', 'OZ', 'O2', 'CB2',
        'HEO', 'VEO', 'EKG', 'EMG'
    ]  # M1: 33. M2: 43.
    """
    CHANNELS = ['POZ', 'PZ', 'PO3', 'PO5', 'PO4', 'PO6', 'O1', 'OZ', 'O2']

    def __init__(self, fs_orig=1000, time_buffer=3, ip_address = '127.0.0.1'):
        '''
        :param fs_orig: int,
            original sampling rate (also called as srate), which depends on device setting.
        :param time_buffer: int (default=30) | float, unit: second,
            time for the data buffer.
        :param channels: int (default=64),
            the number of channels for data collection, which depends on device setting.
        :param ip_address: str,
            the IP of data acquisition computer, e.g. '192.168.36.27'. If None, automatically gets the IP address.
        :param dur_one_packet: float (=0.04 for NeuroScan),
            the time of one packet.
        :param current_ptr: int,
            the pointer of data buffer.
        :param end_flag_trial: the ending flag of the new sample (also called as new trial)
            This end flag got by BaseReadData thread indicated that the BaseProcessRecog thread starts.
            It is used for cutting data from data buffer.
        '''
        Thread.__init__(self)

        self.fs_orig = fs_orig
        self.channels = len(self.CHANNELS)
        self.time_buffer = time_buffer
        self.n_points_buffer = int(round(fs_orig * time_buffer))
        # self.ip_address = socket.gethostbyname(socket.gethostname()) if ip_address is None else ip_address
        self.ip_address = ip_address
        # self.end_flag_trial = end_flag_trial
        self.event_thread_read = Event()
        self.event_thread_read.clear()
        self.data_buffer = zeros((self.channels + 1, self.n_points_buffer))  # data buffer
        # self.data = zeros_like(self.data_buffer)

        self._port = 4000
        self._dur_one_packet = 0.04  # unit: second
        self.n_points_packet = int(round(fs_orig * self._dur_one_packet))
        self.packet_data_bytes = (self.channels+1) * self.n_points_packet * 4
        self.current_ptr = 0
        # self.exist_ptr = 0
        self.s_client = None
        # flag_label[0] represents whether the tag value at last moment is low. flag_label[1] stores the tag value of the last moment.
        self.flag_label = array([0, 0])
        self._ptr_label = 0  # used for recoding location of the packet containing end_flag_trial.

        self._unpack_data_fmt = '<' + str((self.channels + 1) * self.n_points_packet) + 'i'  # big endian
        # self._unpack_data_fmt = '<' + (str(self.channels) + 'i') * self.n_points_packet
        # self.chan_used = ['POZ', 'PZ', 'PO3', 'PO5', 'PO4', 'PO6', 'O1', 'OZ', 'O2']
        self.nUpdate = 0

    def connect_tcp(self):
        '''
        Initialize TCP and Connect with EEG device.
        :return:
            self.s_client: object of socket.
        '''
        self.s_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SEND_BUF_SIZE = self.packet_data_bytes  # unit: bytes
        RECV_BUF_SIZE = self.packet_data_bytes * 9  # unit: bytes
        time_connect = perf_counter()
        self.shutdown_flag = Event()
        self.shutdown_flag.set()
        for i in range(5):
            try:
                sleep(1.5)
                self.s_client.connect((self.ip_address, self._port))
                print('Connect Successfully.')
                # Get current size of the socket's send buffer
                # buff_size = self.s_client.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)  # 8192
                self.s_client.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
                self.s_client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SEND_BUF_SIZE)
                self.s_client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_BUF_SIZE)

                buff_size_send = self.s_client.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF)
                buff_size_recv = self.s_client.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
                print('Current recv buffer size is {} bytes, send buff size is {} bytes.'.format(buff_size_recv, buff_size_send))
                break
            except:
                print('The {}-th Connection fails, Please check params (e.g. IP address).'.format(i+1))
                if i == 4:
                    print('The %s-th Connection fails, program exits.')
                    time_connect = perf_counter() - time_connect
                    print('Consuming time of Connection is {:.4f} seconds.'.format(time_connect))
                    self.s_client.close()

    def start_acq(self):
        # start_acq_command: 67, 84, 82, 76, 0, 2, 0, 1, 0, 0, 0, 0
        # start_get_command: 67, 84, 82, 76, 0, 3, 0, 3, 0, 0, 0, 0
        # start collecting data
        self.s_client.send(pack('12B', 67, 84, 82, 76, 0, 2, 0, 1, 0, 0, 0, 0))  # start acq
        header_packet = self._recv_fixed_len(24)
        # start getting data
        print('Start getting data from buffer by TCP/IP.')
        self.s_client.send(pack('12B', 67, 84, 82, 76, 0, 3, 0, 3, 0, 0, 0, 0))  # start get data

    def stop_acq(self):
        self.s_client.send(pack('12B', 67, 84, 82, 76, 0, 3, 0, 4, 0, 0, 0, 0))  # stop getting data
        sleep(0.001)
        self.s_client.send(pack('12B', 67, 84, 82, 76, 0, 2, 0, 2, 0, 0, 0, 0))  # stop acq
        self.s_client.send(pack('12B', 67, 84, 82, 76, 0, 1, 0, 2, 0, 0, 0, 0))  # close connection
        self.s_client.close()

    def get_data(self):
        '''
        Get a new package and Convert the format (i.e. vector) to 2-D matrix.
        :return: self.new_data: 2-D ndarray,
            axis 0: all EEG channels + label channel. The last row is the label channel.
            axis 1: the time points.
        '''
        t = perf_counter()
        packet_data_bytes = self.packet_data_bytes
        channels = self.channels
        _recv_fixed_len = self._recv_fixed_len
        tmp_header = _recv_fixed_len(12)
        # details_header = self._unpack_header(tmp_header)
        details_header = _unpack_header(tmp_header)

        if details_header[-1] != packet_data_bytes:
            raise ValueError('The .ast template is not matched with class Variable CHANNELS. Please RESET CHANNELS.')


        # 2-D: (EEG channels + label channel) * time points (i.e. =40 for 1000Hz sampling rate)
        t1 = perf_counter()
        bytes_data = _recv_fixed_len(packet_data_bytes)
  
        new_data_trans = asarray(unpack(self._unpack_data_fmt, bytes_data)).reshape((-1, channels + 1)).T
        new_data_temp = empty(new_data_trans.shape, dtype=float)
        new_data_temp[:-1, :] = new_data_trans[:-1, :] * 0.0298  # unit: μV


        t2 = perf_counter()
        new_data_temp[-1, :] = zeros(40)
        loc_label = arange(channels * 4, packet_data_bytes, (channels + 1) * 4)
        if len(loc_label) != new_data_trans.shape[1]:
            raise ValueError('An Error occurred, generally because the .ast template is not matched with CHANNELS.')

        flag_label = self.flag_label
        for idx_time, loc_bytes in enumerate(loc_label):
            label_value = bytes_data[loc_bytes]
            if label_value != 0 and flag_label[0] == 0:  # rising edge of TTL voltage
                self.flag_label[0] = 1
                self.flag_label[1] = label_value
                new_data_temp[-1, idx_time] = label_value
            elif label_value != 0 and flag_label[0] == 1 and flag_label[1] == label_value:
                new_data_temp[-1, idx_time] = 0
            elif label_value == 0 and flag_label[0] == 1:
                self.flag_label[0] = 0
        return new_data_temp



    def is_activated(self):
        # return np.any(self.new_data[-1, :] == self.end_flag_trial)
        pass

    def close_connection(self):
        self.s_client.close()

    #TODO 加快该部分代码速度
    def _recv_fixed_len(self, n_bytes):
        b_data = b''
        flag_stop_recv = False
        b_count = 0
        recv = self.s_client.recv
        while not flag_stop_recv:
            try:
                tmp_bytes = recv(n_bytes - b_count)
            except socket.timeout:
                raise ValueError('No data is Getted.')

            if b_count == n_bytes or not tmp_bytes:
                flag_stop_recv = True

            b_count += len(tmp_bytes)
            b_data += tmp_bytes
        return b_data


    def _unpack_header(self, header_packet):
        # header for a packet
        chan_name = unpack('>4s', header_packet[:4])
        w_code = unpack('>H', header_packet[4:6])
        w_request = unpack('>H', header_packet[6:8])
        packet_size = unpack('>I', header_packet[8:])
        return (chan_name[0].decode('utf-8','ignore'), w_code[0], w_request[0], packet_size[0])


    def _unpack_data(self, data_packet):
        # data for a packet, bytes stream
        data_trans = asarray(unpack(self._unpack_data_fmt, data_packet)).reshape((-1, self.channels + 1)).T
        return data_trans
        

    def run(self):
        lock_read = Lock()
        get_data = self.get_data
        update_buffer = self.update_buffer
        while True:
            # rs, _, _ = select.select([self.s_client], [], [], 12)  # Make sure the connection state
            # if not rs:
            #     raise ValueError('Connection Failed, the tcp/ip may be unstable.')
            if self.s_client:  # rs[0] ==
                lock_read.acquire()
                t1 = perf_counter()
                try:
                    new_data = get_data()
                except:
                    print('Some problems have arisen, can not receive data from socket.')
                    lock_read.release()
                    self.s_client.close()
                else:
                    update_buffer(new_data)
                    #print('Consuming time to get a packet is {:.4f} ms.'.format((perf_counter() - t1) * 1000))
                    lock_read.release()


    def update_buffer(self,new_data):
        '''
        Update data buffer when a new package arrived,40 points
        '''
        t = perf_counter()
        n_points_buffer = self.n_points_buffer
        current_ptr = self.current_ptr
        self.data_buffer[:,mod(arange(current_ptr, current_ptr + 40), n_points_buffer)] = new_data
        self.current_ptr = mod(current_ptr + 40, n_points_buffer)
        self.nUpdate = self.nUpdate+40
        # print('update_buffer:')
        # print(perf_counter() - t)


    def get_buffer_data(self):
        data_buffer = self.data_buffer
        current_ptr = self.current_ptr
        data = hstack([data_buffer[:, current_ptr:], data_buffer[:, :current_ptr]])
        return data


    def get_bufferNupdate(self):
        return self.nUpdate


    def set_bufferNupdate(self,nUpdate):
        self.nUpdate = nUpdate

    
    def stop(self):
        print("Data server connection has stopped")
        self.shutdown_flag.clear()


    def reset_buffer(self):
        '''
        Reset data buffer.
        '''
        self.data_buffer = zeros((self.channels + 1, self.n_points_buffer))  # data buffer
        self.current_ptr = 0
        self.nUpdate = 0



    def channel_selected(self,data):
        '''
        Select channel to use for the next processing step.
        :return:
            self.raw_data:
                the format is same with method __init__ of class BaseProcessRecog.
            self.evt: 2-D ndarray,
                format - n_events * 2(i.e. value and latency)
        '''
        # idx_loc = list()
        # if isinstance(self.chan_used, list):
        #     for _, char_value in enumerate(self.chan_used):
        #         idx_loc.append(self.CHANNELS.index(char_value.upper()))

        idx_loc = [0, 2, 3, 4, 5, 6, 7, 8]
        raw_data = data[idx_loc, :]
        evt_value_buff = data[-1, :]
        return raw_data, evt_value_buff








