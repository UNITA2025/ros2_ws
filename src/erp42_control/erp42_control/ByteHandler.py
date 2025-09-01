#! /usr/bin/env python3

import struct
import numpy as np
from interfaces_control_pkg.msg import ErpCmdMsg, ErpStatusMsg # msg 정의한 패키지명으로 변경


def Packet2ErpMsg(_byte: bytes) -> ErpStatusMsg:
    formated_packet = struct.unpack('<BBBBBBhhBiBBB', _byte)
    msg = ErpStatusMsg()
    msg.control_mode = formated_packet[3]
    msg.e_stop = bool(formated_packet[4])
    msg.gear = formated_packet[5]
    msg.speed = formated_packet[6]
    msg.steer = -formated_packet[7]
    msg.brake = formated_packet[8]
    msg.encoder = int(formated_packet[9])
    msg.alive = formated_packet[10]
    return msg


def ErpMsg2Packet(_msg: ErpCmdMsg, _alive: np.uint8) -> list:
    header = "STX".encode()
    tail="\r\n".encode()

    data = struct.pack(
        ">BBBHhBB", 1,
        _msg.e_stop,
        _msg.gear,
        _msg.speed,
        _msg.steer,
        _msg.brake,
        _alive
    )
    packet = header + data + tail
    return packet


def main():
# 여기에 실행 코드 작성
    print("ByteHandler started")
# 또는 필요한 동작 호출
# 예: some_handler.start()

if __name__ == "__main__":
    main()
