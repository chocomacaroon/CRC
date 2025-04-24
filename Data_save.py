C:\Users\kth42\Desktop\CRC2024\FInal\사고\데이터측정실험\wifi_bno_datacollect.py
import socket
import threading
import os

# 서버 소켓을 설정합니다.
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8889))  # 모든 인터페이스에서 8888 포트로 대기
server_socket.listen(15)  # 최대 15개의 연결 대기

connected_devices = {}
lock = threading.Lock()
received_data_buffer = {}

# 파일을 저장할 폴더 경로
folder_path = 'data_logs'
# 폴더가 존재하지 않으면 생성합니다.
if not os.path.exists(folder_path):
    os.makedirs(folder_path)

def handle_client(client_socket, client_address):
    try:
        # 클라이언트로부터 ID를 수신합니다.
        device_id = client_socket.recv(1024).decode('utf-8').strip()
        print(f"장치 {device_id} ({client_address}) 연결됨")

        with lock:
            connected_devices[device_id] = client_socket
            received_data_buffer[device_id] = ""

        if device_id.startswith("app"):
            handle_app_device(client_socket, client_address)
        else:
            handle_number_device(client_socket, device_id, client_address)

    except Exception as e:
        print(f"데이터 수신 중 오류 발생: {e}")
    finally:
        with lock:
            if device_id in connected_devices:
                del connected_devices[device_id]
            if device_id in received_data_buffer:
                del received_data_buffer[device_id]
        client_socket.close()
        print(f"장치 {device_id} ({client_address}) 연결 종료")


def handle_app_device(client_socket, client_address):
    try:
        while True:
            # app 장치로부터 명령을 수신합니다.
            command = client_socket.recv(1024).decode('utf-8').strip()
            print(f"app 장치로부터 수신된 명령: {command}")

            if command.upper() in ("START", "STOP"):
                with lock:
                    for device_id, device_socket in connected_devices.items():
                        if device_id != "app":
                            try:
                                device_socket.send(command.upper().encode('utf-8'))
                            except Exception as e:
                                print(f"장치 {device_id}에 {command} 메시지를 보내는 중 오류 발생: {e}")
            if not command:
                with lock:
                    if "app" in connected_devices:
                        del connected_devices["app"]
                client_socket.close()
                print(f"장치 app ({client_address}) 연결 종료")
                break

    except Exception as e:
        print(f"app 장치 처리 중 오류 발생: {e}")


def handle_number_device(client_socket, device_id, client_address):
    try:
        while True:
            # 숫자 장치로부터 데이터를 수신합니다.
            received_data = client_socket.recv(1024).strip().decode('utf-8')
            if not received_data:
                with lock:
                    if device_id in connected_devices:
                        del connected_devices[device_id]
                    if device_id in received_data_buffer:
                        del received_data_buffer[device_id]
                client_socket.close()
                print(f"장치 {device_id} ({client_address}) 연결 종료")
                break

            # Buffer에 수신된 데이터 추가
            with lock:
                received_data_buffer[device_id] += received_data

            if "END!!!" in received_data_buffer[device_id]:
                # 'END!!!'를 찾으면 전체 데이터를 파일에 저장
                with lock:
                    file_path = os.path.join(folder_path, "total_data.txt")
                    with open(file_path, "a") as file:
                        file.write(received_data_buffer[device_id] + "\n")
                    # 저장 완료 메시지 출력
                    print(f"데이터가 {file_path} 파일에 저장되었습니다.")
                    # 파일 내용을 출력
                    with open(file_path, "r") as file:
                        print("현재 파일 내용:")
                        print(file.read())
                    # 버퍼 초기화
                    received_data_buffer[device_id] = ""

    except Exception as e:
        print(f"숫자 장치 처리 중 오류 발생: {e}")


print("서버가 시작되었습니다. 연결 대기 중...")

while True:
    # 클라이언트 연결을 수락합니다.
    client_socket, client_address = server_socket.accept()

    # 새로운 스레드를 생성하여 클라이언트를 처리합니다.
    client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
    client_thread.start()
