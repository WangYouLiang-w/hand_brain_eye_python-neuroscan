import socket
from cv2 import initUndistortRectifyMap
# 建立服务端
ClientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ClientIp = socket.gethostbyname(socket.gethostname())    #获取本地ip
ClientAddr = (ClientIp, 8848)                      #设置端口号
ClientSocket.bind(ClientAddr)

while True:
    send_data = input("请输入要发送的数据：")
    if send_data == 'exit':
        break
    ClientSocket.sendto(send_data.encode("gbk"),('192.168.137.1',8847)) # 由于接收是在windows上，而windows中默认编码是gbk

# 关闭套接字
ClientSocket.close()

