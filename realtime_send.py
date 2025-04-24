#C:\Users\kth42\Desktop\CRC2024\FInal\사고\최종\final_240926.py
import socket
import threading
import os
import time
import numpy as np
import math
import re
import requests
import json
from collections import deque
from scipy.spatial.transform import Rotation as R
# 초기값 저장용 변수

# 서버 소켓을 설정합니다.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8889))  # 모든 인터페이스에서 8888 포트로 대기
server_socket.listen(18)  # 최대 17개의 연결 대기

# 필요 버퍼
buffer_size = 8
check_page = False
check_buffer = {}
connected_devices = {}
received_data_buffer = {'altitude': -99999}
lock = threading.Lock()

# 고도 값을 저장할 큐 생성 (최대 15개의 값, 초기 값 -99999로 설정)
altitude_queue = deque([-99999] * 15, maxlen=15)

# 파일을 저장할 폴더 경로
folder_path = 'data_logs'
# 폴더가 존재하지 않으면 생성합니다.
if not os.path.exists(folder_path):
    os.makedirs(folder_path)
############################################
def quaternion_inverse(q):
    """주어진 쿼터니언의 역쿼터니언을 계산합니다."""
    q_conjugate = np.array([q[0], -q[1], -q[2], -q[3]])
    q_norm_squared = np.dot(q, q)
    return q_conjugate / q_norm_squared

def quaternion_multiply(q1, q2):
    """두 쿼터니언의 곱을 계산합니다."""
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    w = w1*w2 - x1*x2 - y1*y2 - z1*z2
    x = w1*x2 + x1*w2 + y1*z2 - z1*y2
    y = w1*y2 - x1*z2 + y1*w2 + z1*x2
    z = w1*z2 + x1*y2 - y1*x2 + z1*w2
    return np.array([w, x, y, z])

def quaternion_to_euler_angles(q):
    """쿼터니언을 유로 각으로 변환합니다 (XYZ 순서)."""
    rotation = R.from_quat([q[1], q[2], q[3], q[0]])  # scipy는 x, y, z, w 순서를 사용합니다.
    euler_angles = rotation.as_euler('xyz', degrees=True)  # 각도 단위로 반환
    return euler_angles

def calculate_rotation_components(user_quaternion):
    # 사용자 입력 쿼터니언 생성
    w, x, y, z = user_quaternion
    rotation = R.from_quat([x, y, z, w])

    # 회전 축과 각도 추출
    angle = rotation.magnitude()
    axis = rotation.as_rotvec() / angle if angle != 0 else np.zeros(3)

    # X, Y, Z 축에 대한 회전 분량 계산
    return np.degrees(angle * axis[0]),np.degrees(angle * axis[1]),np.degrees(angle * axis[2])


def update_altitude_queue(state, new_altitude):

    altitude_queue.append(new_altitude)

    # 기본 상태는 'S'
    # print(len(altitude_queue))
    # 큐에 15개의 값이 있을 때, 첫 번째 값과 마지막 값을 비교하여 차이가 15 이상이면 상태를 'C'로 변경
    if len(altitude_queue) == 15:
        first_altitude = altitude_queue[0]
        last_altitude = altitude_queue[-1]

        altitude_difference = first_altitude-last_altitude
        print(altitude_queue)

        if altitude_difference >= 2:
            state = "C"
        kakao_send("!!추락사고 발생!!")
    return state

# 마지막 호출 시간을 저장할 전역 변수
last_response_time = time.time()


def generate_response():
    while not check_page:
        pass
    test_pairs = [
        ("01", "02")
        # ("02", "04"),
        # ("03", "05")
    #     ("05", "06"),
    #     ("06", "07"),
    #     ("03", "08"),
    #     ("08", "09"),
    #     ("09", "10"),
    #     ("04", "11"),
    #     ("11", "12"),
    #     ("12", "13"),
    #     ("04", "14"),
    #     ("14", "15"),
    #     ("15", "16"),
    ]
    # test_pairs=[("01", "02")]
    data_to_send = ""
    state ="S"
    # 상대각도 처리
    for i, (part1_id, part2_id) in enumerate(test_pairs):
        index_str = f"{i + 1:02d}"
        w1, x1, y1, z1 = received_data_buffer[part1_id]
        w2, x2, y2, z2 = received_data_buffer[part2_id]
        if np.allclose(received_data_buffer[part1_id], [1, 0, 0, 0]):
            q_rel = received_data_buffer[part2_id]
        else:
            q_inv = quaternion_inverse(received_data_buffer[part1_id])
            q_rel = quaternion_multiply(q_inv, received_data_buffer[part2_id])

        d1,d2,d3 = quaternion_to_euler_angles(q_rel)
        d1, d2, d3= int(d1+180/30)-6,int(d2+180/30),int(d3+180/30)
        # print(f"roll_diff: {round(x1, 2):04}, pitch_diff: {round(y1, 2):04}, yaw_diff: {round(z1, 2):04}",end="\t")
        # print(f"roll_diff: {round(x2, 2):04}, pitch_diff: {round(y2, 2):04}, yaw_diff: {round(z2, 2):04}",end="\t")
        # print(f"roll_diff: {d1}, pitch_diff: {d2}, yaw_diff: {d3}")
        # 01과 02에 대한 출력
        if part1_id == "01" and part2_id == "02":
            print(f"roll_diff: {round(d1, 2):04}, pitch_diff: {round(d2, 2):04}, yaw_diff: {round(d3, 2):04}")
        if part1_id == "01" and part2_id == "02":   #머리
            if d2 >4 or d3>2:
                state="D"
        if part1_id == "05" and part2_id == "06":   #왼쪽 팔꿈치
            if d3>0 or d1<-1 or d1>1 or d2<-1 or d2>1:
                state="D"
        if part1_id == "08" and part2_id == "09":   #오른쪽 팔꿈치
            if d3>0 or d1<-1 or d1>1 or d2<-1 or d2>1:
                state="D"
        # if part1_id == "11" and part2_id == "12":   #왼쪽 무릎
        #     if d2 > 230 or d1>210 or d1<150:
        #         state="D"
        # if part1_id == "14" and part2_id == "15":   #오른쪽 무릎
        #     if d2 > 230 or d1>210 or d1<150:
        #         state="D"

        #추락 상황
        if received_data_buffer:
            new_altitude = float(received_data_buffer["altitude"])
            state = update_altitude_queue(state, new_altitude)
            # print(state)
            # print(altitude_queue)

        if i == len(test_pairs) - 1:
            data_to_send += f"{state}01:{d1:.8f},{d2:.8f},{d3:.8f};S02:000,000,000;S03:000,000,000;S04:000,000,000;S05:000,000,000;S06:000,000,000;S07:000,000,000;S08:000,000,000;S09:000,000,000;S10:000,000,000;S11:000,000,000;S12:000,000,000;S13:000,000,000;S14:000,000,000"
        else:
            data_to_send += f"{state}{index_str}:{d1:.8f},{d2:.8f},{d3:.8f};"

    if "D" in data_to_send:
        danger_joint_num = [data_to_send[i+1:i+3] for i in range(len(data_to_send)) if data_to_send[i] == a]
        kakao_send("!!골절사고 발생!!" + "\n".danger_joint())
    if "C" in data_to_send:
        kakao_send("!!추락사고 발생!!")
    data_to_send += "!"
    return data_to_send

def send_continuous_data(client_socket, stop_event):
    while not stop_event.is_set():
        try:
            response = generate_response()  # 응답 데이터를 생성
            client_socket.send(response.encode('utf-8'))  # 클라이언트에 응답 전송
            time.sleep(0.02)  # 20ms 대기
        except socket.error as e:
            print(f"데이터 전송 중 오류 발생: {e}")
            break
def handle_client(client_socket, client_address):
    # 클라이언트로부터 ID를 수신합니다.
    device_id = client_socket.recv(32).decode('utf-8').strip()
    print(f"장치 {device_id} ({client_address}) 연결됨")
    check_buffer[device_id] = True
    with lock:
        connected_devices[device_id] = client_socket
    if device_id.startswith("app"):
        del check_buffer[device_id]
        handle_app_device(client_socket, client_address)
    elif device_id.startswith("01"):
        handle_01_device(client_socket, device_id, client_address)
    else:
        handle_number_device(client_socket, device_id, client_address)

    with lock:
        if device_id in connected_devices:
            del connected_devices[device_id]
        if device_id in received_data_buffer:
            del received_data_buffer[device_id]
        client_socket.close()
        print(f"장치 {device_id} ({client_address}) 연결 종료")
def handle_app_device(client_socket, client_address):
    stop_event = threading.Event()  # 데이터를 전송할 스레드를 제어할 이벤트
    continuous_thread = None  # 데이터를 전송할 스레드

    try:
        while True:
            # app 장치로부터 명령을 수신합니다.
            command = client_socket.recv(1024).decode('utf-8').strip()
            print(f"app 장치로부터 수신된 명령: {command}")

            if command.upper() == "START":
                print("데이터 전송 시작")
                # 아두이노 장치로 START 명령을 전송
                for device_id, device_socket in connected_devices.items():
                    if device_id != "app":
                        try:
                            device_socket.send(command.upper().encode('utf-8'))
                        except Exception as e:
                            print(f"장치 {device_id}에 START 메시지를 보내는 중 오류 발생: {e}")
                # 데이터 전송을 시작할 스레드
                if continuous_thread is None or not continuous_thread.is_alive() :
                    stop_event.clear()  # 데이터 전송을 중단하지 않도록 이벤트 해제
                    continuous_thread = threading.Thread(target=send_continuous_data, args=(client_socket, stop_event))
                    continuous_thread.start()

            elif command.upper() == "STOP":
                print("데이터 전송 중지")
                # 아두이노 장치로 STOP 명령을 전송
                for device_id, device_socket in connected_devices.items():
                    if device_id != "app":
                        try:
                            device_socket.send(command.upper().encode('utf-8'))
                        except Exception as e:
                            print(f"장치 {device_id}에 STOP 메시지를 보내는 중 오류 발생: {e}")

                # 데이터 전송 중지
                if continuous_thread is not None and continuous_thread.is_alive():
                    stop_event.set()  # 데이터 전송을 중단하도록 이벤트 설정
                    continuous_thread.join()  # 스레드가 완전히 종료될 때까지 대기
                    continuous_thread = None

            if not command:
                if "app" in connected_devices:
                    del connected_devices["app"]
                client_socket.close()
                print(f"장치 app ({client_address}) 연결 종료")
                break

    except Exception as e:
        print(f"app 장치 처리 중 오류 발생: {e}")
    finally:
        # 연결 종료 시에도 STOP 명령을 보냄
        if continuous_thread is not None and continuous_thread.is_alive():
            stop_event.set()
            continuous_thread.join()

def handle_01_device(client_socket, device_id, client_address):
    buffer_limit = 128  # 수신 버퍼 크기
    chunk = ''
    init_x, init_y, init_z = 0, 0, 0
    init_flag = True
    while True:
        # 숫자 장치로부터 데이터를 수신합니다.
        chunk += client_socket.recv(buffer_limit).decode('utf-8')
        # print(chunk)
        # 1번 디바이스에서 고도 값과 쿼터니언 값을 분리하는 패턴
        # 정규 표현식 패턴: 고도와 quaternion 값을 구분
        pattern = re.compile(r'!!!(\d+\.\d+-?),(\d+\.\d+-?),(\d+\.\d+-?),(\d+\.\d+-?),(\d+\.\d+-?)!!!')
        matches = pattern.search(chunk[::-1])
        if matches and check_buffer[device_id]:
            altitude = matches.group()[::-1][3:].split(",")[0]  # 고도 값 추출
            received_data_buffer['altitude'] = altitude
            # 고도 값을 따로 저장하고 quaternion 값은 기존 로직에 맞게 처리
            if init_flag:
                init_x, init_y, init_z = calculate_rotation_components(list(map(float, matches.group()[::-1][3:-3].split(",")[1:])))
                init_flag=False
            x, y, z = calculate_rotation_components(list(map(float, matches.group()[::-1][3:-3].split(",")[1:])))
            # received_data_buffer[device_id] = [(x-init_x+180)%360, (y-init_y+180)%360, (z-init_z+180)%360]
            # received_data_buffer[device_id] = x+180, y+180, z+180
            received_data_buffer[device_id] = list(map(float, matches.group()[::-1][3:-3].split(",")[1:]))
            check_buffer[device_id] = False  # 데이터가 처리되었음을 알림
            #print(f"1번 디바이스로부터 받은 고도: {altitude}, quaternion: {','.join(match[1:])}")
            # 남은 데이터는 다시 chunk에 넣음
            chunk = chunk[chunk.rfind('!!!'):]  # 남은 데이터는 유지

def handle_number_device(client_socket, device_id, client_address):
    buffer_limit = 128  # 수신 버퍼 크기
    chunk = ''
    init_x, init_y, init_z = 0, 0, 0
    init_flag = True
    while True:
        # 숫자 장치로부터 데이터를 수신합니다.
        chunk += client_socket.recv(buffer_limit).decode('utf-8')
        # print(chunk)
        pattern = re.compile(r'!!!(\d+\.\d+-?),(-?\d+\.\d+-?),(-?\d+\.\d+-?),(-?\d+\.\d+-?)!!!')
        matches = pattern.search(chunk[::-1])
        if matches and check_buffer[device_id]:
            if init_flag:
                init_x, init_y, init_z = calculate_rotation_components(list(map(float, matches.group()[::-1][3:-3].split(","))))
                init_flag = False
            x, y, z = calculate_rotation_components(list(map(float, matches.group()[::-1][3:-3].split(","))))
            # received_data_buffer[device_id] = [(x-init_x+180)%360, (y-init_y+180)%360, (z-init_z+180)%360]
            # received_data_buffer[device_id] = x + 180, y + 180, z + 180
            received_data_buffer[device_id] = list(map(float, matches.group()[::-1][3:-3].split(",")))
            check_buffer[device_id] = False  # 데이터가 처리되었음을 알림
            # 남은 데이터는 다시 chunk에 넣음
            chunk = chunk[chunk.rfind('!!!'):]  # 남은 데이터는 유지

def make_page():
    global check_page
    while True:
        if all(value is False for value in list(check_buffer.values())) and len(check_buffer) > 0:
            for device_ID in received_data_buffer:
                if device_ID != 'altitude':
                    check_page = True
                    check_buffer[device_ID] = True

def kakao_send(msg):
    print("kakao_send",msg,"함수 실행")

    # GPS 변수 예시
    x = 127.423084873712  # 경도
    y = 37.0789561558879  # 위도
    address = get_address_from_gps(x, y)
    print(address)

    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": "6adb7822f43ec749dc87eed31908706a",  # API 앱키
        "refresh_token": "2fFQIBwQe1tj8diMD9uI9tJbXXT3l-7AAAAAAgoqJVAAAAGSF3-pr5gXPJRhmZ-F"  # refresh token
    }
    response = requests.post(url, data=data)
    tokens = response.json()
    # kakao_code.json 파일 저장
    with open("kakao_code.json", "w") as fp:
        json.dump(tokens, fp)

    url="https://kapi.kakao.com/v2/api/talk/memo/default/send"

    # kapi.kakao.com/v2/api/talk/memo/default/send
    headers={
        "Authorization" : "Bearer " + tokens['access_token']
    }

    data = {
        "template_object": json.dumps({
            "object_type": "location",
            "content":{
                "title": f"!!!사고감지!!! {msg}",
                "description": "",
                "image_url": "https://lh3.googleusercontent.com/fife/ALs6j_FzKBRkENjDISMtW_Apaa_FakeS_jWukWKWSjrafYZ1H-UYqwvicXF1KJ8lBGtEkTtOa2EdSS6w25DkktVrf_AwIe5eDAfkIQ9n04XgSy9jR0XweV24oZabqC0pHLFDjU-o8DaBwqUROaKcMoYMvjEX9hVoYJ834MJ9_GTB2TlilCFCW7ISq-oTYc0igEXp14b45Zq5hGsqz_gde5GA3zwyOCo-0XBf9zGyVSUU-uqZ_iI-pYpkPQvrwEhNuL_bZCqxoeA_oEzLuMbYnc-9wpwYPBdNvRbp8L-k5tNlsSTJdh0t8tLHdS2WeBKGsh2Yt87T4ltWybacYLE4hSrKha4Kr2dqEoOWKi4y9nrj98zG_LXPRWvuiJlv0jYkzV4G-DjR9K4r91g3y5hU7s8kvDCBZsHS099PcYcRXsSpfD2zr2AqCQ3w0NvJbXPiCMpIF4CaD_FWeHF4zsyVZz_1A9r40huGmvoSv18-dMgJDjIvUAb_CQRVh1hD5ydW6iNntG5j7qoJqx251UbtnCOhKgP0bo-hEG0PVeEI8PjzgoVoxTlrlhPwIh8Z_Qjgc-vOpzAFs6m7gI5P1PqT2EZAQ8mdDMfXyyYivMRqduTqsVyYj4W9D_osQv5XLCNJobrsot8Gh96QPqGKlD-GpLFOD7sNSOlhvUBnxAP6_t_QOQIrEoWSBoUfbxqujs0BvKACQrfH6Asv91oQggXHHckqt90KYGsuMmpGTXiKc4i5yrWjk5NDy2uJx7xr-aMp7YyB4Lu8MMfD_NlTcBu7TukAVLnDGW8lFI5_C_TirWAsPrrhPtCN_ICnyGsiPTXMUJGRtawFoYaoU8l11SYl4fSlg0VgISq_4M5C9MUuTKrSZsJcX5cIGQ6U-Uf3vj9u7201FeyIohf0TBR17pfkt1V1BHtBW4cerSudeMjSMiKC7DFpvwA_HM06gMadzvxrmcZkyQ7qBEBUdeSsioznbtd-Q74EDdv2Kp3A67NVPZyAp4kFUVWNq4W8DJGApKgLOvrk_ncDtLLI13kW2ozaVwd1PvHeDMxPPXQOvdG3LdFF44wRMXZrqKN3zDJaCVeepctc47agX4139ZNoa5fwTYMiSMdJEzNpl1aY00y8cTsJ1rqb2yYPbPmXZSvPLtzBFZIVFozwEwePjbU5aZcA_3D8qYCpHV3tI2ZY69r3ZuJzFIUjmSK0A_PyJDkLeL0wJ0599A9VOn2nIGTEJqZB7mGUReedHim6sU-YSnRstwgGh1lTTNPWLAw1DRVybK4CyxxVcf7BX9xXCoLpCjQFoJeNP40w46GR5MF8czJuTJu-cK9I9SO9YDSGY8Kkzm-Y4ocpOMtRR0khF6OWseK1uJ4IQhjoZ2nD6M-_aU4pCoyte96ehd4Z8m8067hp1oT1OY8EKk8Blg7xkMf7qLPLtYdjzaxfgQzdtD1BVcwj9R009RsbJUrTQ9jVaWnc0da-2qpg_IEhRXoyHUrVGAeEMto4Xpjus78Z6zap25IJNuwZnezq9e0FEcYeI8scA9zovg9nU_pfG63gqaV3VYVhcfn-7sDvX9t3Hxl0SUeDb2tHZDjcUW3r-ui2FrbzPDDGH9CC8jZwYfCSXa-Jd1-cdqbrqUUmVMRiC8eAVUau9COes-y8Aiis0TARbw-tV6U=w958-h892",
                "image_width": 800,
                "image_height": 800,
                "link":{
                    "web_url": "https://naver.com",
                    "mobile_web_url": "https://naver.com",
                    "android_execution_params": "platform=android",
                    "ios_execution_params": "platform=ios"
                }
            },
            "buttons": [
                {
                    "title": "웹으로 보기",
                    "link":{
                        "web_url": "https://youtube.com",
                        "mobile_web_url": "https://youtube.com"
                    }
                }
            ],
            "address": address,
            "address_title":address
        })
    }

    response = requests.post(url, headers=headers, data=data)
    response.status_code
    print(response.status_code)
    if response.json().get('result_code') == 0:
        print('메시지를 성공적으로 보냈습니다.')
    else:
        print('메시지를 성공적으로 보내지 못했습니다. 오류메시지 : ' + str(response.json()))

def get_address_from_gps(x, y):
    # 좌표값 (x: 경도, y: 위도)
    params = {
        'x': str(x),  # 경도
        'y': str(y),  # 위도
        'input_coord': 'WGS84'
    }

    # Kakao API URL
    url = 'https://dapi.kakao.com/v2/local/geo/coord2address.json'

    # 요청 헤더 설정 (Authorization에 KakaoAK + REST API 키 사용)
    headers = {
        'Authorization': f'KakaoAK {REST_API_KEY}'
    }

    # GET 요청 보내기
    response = requests.get(url, headers=headers, params=params)

    # 응답 결과 확인
    if response.status_code == 200:
        result = response.json()
        # 주소 정보가 있을 경우 반환
        if 'documents' in result and result['documents']:
            address = result['documents'][0]['address']['address_name']
            road_address = result['documents'][0].get('road_address', None)
            if road_address:
                return f"주소: {address}, 도로명 주소: {road_address['address_name']}"
            else:
                return f"주소: {address}"
        else:
            return "해당 좌표에 대한 주소 정보를 찾을 수 없습니다."
    else:
        return f"Error: {response.status_code}, {response.text}"

if __name__ == "__main__":
    print("서버가 시작되었습니다. 연결 대기 중...")
    get_data = threading.Thread(target=make_page)
    get_data.start()
    while True:
        # 클라이언트 연결을 수락합니다.
        client_socket, client_address = server_socket.accept()
        # 새로운 스레드를 생성하여 클라이언트를 처리합니다.
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()
