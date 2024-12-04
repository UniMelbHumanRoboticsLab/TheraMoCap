import sys
import time
import os
import socket
from blessed import Terminal
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import mo_cap.vr.openvr_util as openvr_util
from mo_cap.xsens.xsens_udp_util import parse_header,parse_UL_joint_angle,parse_time


"start the console terminal for nice logging"
term = Terminal()

"Start UDP Port for XSENS"
UDP_IP = "127.0.0.3"
UDP_PORT = 9764
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

"start the VR platform"
v = openvr_util.triad_openvr()
tracker_details = ["=========VIVE Details=========="] + v.get_discovered_objects() +["=================="]

"set sampling time"
if len(sys.argv) >= 2:
    interval = 1/70
    num_tracker = int(sys.argv[1])
else:
    interval = 1/70
    num_tracker = 2

"start the logging"
with term.fullscreen():

    # log vive tracker details
    start_row = 0
    for i, message in enumerate(tracker_details):
        print(term.move(i, 0) + term.bold(message))
    # Calculate the starting row for streaming data to maintain initial message
    start_row += len(tracker_details)

    while(True):
        start = time.time()
        txt = "=========VIVE==========\n"
        
        """
        Vive Acquisition
        """
        # notify if a tracker is lost, if not, print euler detail in every tracker
        lost = False
        for i in range(num_tracker):
            txt += f"Tracker {i+1}:"
            pose_euler,t_mat,valid =  v.devices[f"tracker_{i+1}"].get_pose_euler() # return the pose in euler (ZYX) and transformation matrix
            if valid:
                for each in pose_euler:
                    txt += "%8.4f" % each
                    txt += " "
                txt += "\n"
            else:
                txt += " Lost"
                txt += "\n"
                lost = True

        """
        XSENS Acquisition
        """
        txt += "=========XSENS==========\n"
        # loop n times if we are expecting n different UDP packets
        info_num = 2
        for i in range(info_num):
            message, addr = sock.recvfrom(4096)
            header = parse_header(message[0:24]) # parse key info into header first
            if header['message_id'] == 'MXTP20':
                right,left = parse_UL_joint_angle(message=message[24:])
                for key in right.keys():
                    txt += f"{key:15}: {left[key]:8.4f} {right[key]:8.4f}\n"
                # print("RIGHT:",right)
                # print("LEFT:",left)
            elif header['message_id'] == 'MXTP25' and header['character_id'] == 0:
                sampled_time = parse_time(message[-12:])
                # print("\rSampled_time:",sampled_time)
                txt += f"TIME: {sampled_time}\n"
            else:
                continue

        """
        Control Sampling Frequency
        """
        sleep_time = interval-(time.time()-start)
        if sleep_time>0:
            time.sleep(sleep_time)

        """
        Console Log
        """
        sampling_freq = 1/(time.time()-start)
        string = "sampling freq"
        txt += f"{string:15}: {sampling_freq:.4f} Hz"
        print(term.move(start_row, 0) + term.clear_eol() + txt)