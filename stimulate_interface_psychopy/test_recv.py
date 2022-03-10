import socket

from numpy import empty

# 建立服务端
SeverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SeverIp = socket.gethostbyname(socket.gethostname())    #获取本地ip
SeverAddr = (SeverIp, 8847)                      #设置端口号
SeverSocket.bind(SeverAddr)

while True:
    recv_data = SeverSocket.recvfrom(1024)  # recv_data存储元组（接收到的数据，（发送方的ip和port)
    print('i')
    recv_msg = recv_data[0] # 信息内容
    recv_addr = recv_data[1] # 信息地址

    if recv_data is not empty:
        print(' is not empty')
    
    print(recv_data)
    print("信息来自:{} 内容是:{}".format(recv_msg,recv_addr))

SeverSocket.close()


