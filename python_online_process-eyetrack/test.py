# import socket


# client_ip = socket.gethostbyname(socket.gethostname())
# client_addr = (client_ip, 8848)

# char = ['a','b','c','d','e','f','g','h','i','j','k','l']

# command1 = 11
# command2 = 10
# result1 = char[command1]
# result2 = char[command2]
# client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# controlCenterAddr = ('127.0.0.1', 8847)   

# command = result1 + result2
# while True:
#     msg = bytes(str(command), "utf8")
#     client_socket.sendto(msg,controlCenterAddr)


# from typing import Counter


# class Person:
#     def __init__(self,name,weight) -> None:
#         # self.属性 = 形参
#         self.name = name
#         self.weight = weight

#     def __str__(self) -> str:
#         return "我的名字是{}，体重是{}公斤".format(self.name,self.weight)

#     def run(self):
#         print("%s爱跑步，跑步锻炼身体"%self.name)
#         self.weight[0] -= 0.5

#     def eat(self):
#         pass


# weight = [75,65]
# xiaoming = Person("小明",weight)
# print(xiaoming)
# xiaoming.run()
# print(xiaoming)
# print('xiaoming:{}'.format(weight))

# def test(num):
#     print("num:地址%d" % id(num))
#     # 定义字符串
#     result = "hello"
#     print("函数要返回数据的内存地址%d" % id(result))

#     # 返回的数据的引用，并不是数据本身
#     return result

# a = 10
# print("a:地址%d" % id(a))
# # 调用函数，本质是传递的是实参保存数据的引用，而不是实参保存的数据
# r = test(a)
# print("函数返回数据的内存地址%d" % id(r))


#%% test1 （列表和字典是可变类型）
# from gettext import npgettext
# import threading
# import time
# from multiprocessing import Process, Manager
# import numpy as np


# #创建子线程类，继承自 Thread 类
# class my_Thread(threading.Thread):
#     def __init__(self,add):
#         threading.Thread.__init__(self)
#         self.add = add
#     # 重写run()方法
#     def run(self):
#          while True:
#              if self.add[0] == 1:
#                  print('add is {}'.format(self.add))
#                  self.add[0] = 0


# if __name__ == '__main__':
#     #定义为 run() 方法传入的参数
#     my_tuple = [1]
#     #创建子线程
#     mythread = my_Thread(my_tuple)
#     #启动子线程
#     mythread.daemon = True
#     mythread.start()
#     #主线程执行此循环
#     while True:
#         print(my_tuple[0])
#         time.sleep(2)

#%% test 2 (数值是不可变类型)
import threading
import time
from multiprocessing import Process, Manager
import numpy as np


#创建子线程类，继承自 Thread 类
class my_Thread(threading.Thread):
    def __init__(self,add):
        threading.Thread.__init__(self)
        self.add = add
    # 重写run()方法
    def run(self):
         while True:
             if self.add== 1:
                 print('add is {}'.format(self.add))
                 self.add = 0


if __name__ == '__main__':
    #定义为 run() 方法传入的参数
    my_tuple = 1
    #创建子线程
    mythread = my_Thread(my_tuple)
    #启动子线程
    mythread.daemon = True
    mythread.start()
    #主线程执行此循环
    while True:
        print(my_tuple)
        time.sleep(2)