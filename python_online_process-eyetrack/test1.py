
# %% 测试获取时间同步数据

import time
from tobiiresearch.implementation import EyeTracker

# Step1:find eye tracker
found_eyetrakers = EyeTracker.find_all_eyetrackers()      # 寻找通过usb或以太网电缆直接连接到您的计算机的眼动仪，以及连接到与您的计算机相同网络的眼动仪。
my_eyetraker = found_eyetrakers[0]
print("Address:" + my_eyetraker.address)
print("Model:" + my_eyetraker.model)
print("Name(It's OK if this is empty):" + my_eyetraker.device_name)
print("Serial number:" + my_eyetraker.serial_number)

def time_synchronization_data_callback(time_synchronization_data):
     print(time_synchronization_data)

def time_synchronization_data(eyetracker):
    print("Subscribing to time synchronization data for eye tracker with serial number {0}.".
           format(eyetracker.serial_number))
    eyetracker.subscribe_to(EyeTracker.EYETRACKER_TIME_SYNCHRONIZATION_DATA,
                             time_synchronization_data_callback, as_dictionary=True)
 
    # Wait while some time synchronization data is collected.
    time.sleep(2)
 
    eyetracker.unsubscribe_from(EyeTracker.EYETRACKER_TIME_SYNCHRONIZATION_DATA,
                                 time_synchronization_data_callback)
    print("Unsubscribed from time synchronization data.")



if __name__ == '__main__':
    while True:
        time_synchronization_data(my_eyetraker)