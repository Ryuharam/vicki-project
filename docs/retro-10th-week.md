# 1. 서버 프로세스·스레드·메모리 관찰
> 개인 프로젝트 FastAPI 서버를 macOS에서 실행하고, `ps` / `top` 으로 프로세스·스레드·메모리 상태를 관찰한 뒤 동작 변화를 기록

## 1-1. 관찰 환경
| 항목 | 내용 |
|---|---|
| OS | macOS (Darwin) |
| 실행 도구 | `uv` (가상환경 내 Python 실행기) |
| 런타임 | Python 3.14 |
| 서버 | FastAPI + uvicorn (`--reload`) |
| 관찰 도구 | `ps`, `top -pid` |

## 1-2. `ps`

<img width="2650" height="462" alt="Image" src="https://github.com/user-attachments/assets/86240e3a-a564-4b05-9590-bf2cec82dc8b" />


- `--reload` 때문에 내부적으로 멀티프로세싱이 사용됨
- uvicorn 실행 시 `--reload` 옵션을 주면, uvicorn은 코드 변경을 감시하는 프로세스(부모)와 실제 웹 서버를 구동하는 프로세스(자식)를 분리한다.

 
| 역할 | 설명 |
|---|---|
| `uvicorn ... --reload` | 부모 프로세스. 파일 변경 감시 담당 |
| `multiprocessing.spawn` | 자식 프로세스. 코드가 바뀌면 이 자식을 죽이고 다시 `spawn`(생성) |
| `multiprocessing.resource_tracker` | 파이썬 멀티프로세싱 모듈이 생성하는 관리용 프로세스. 자식이 갑자기 종료되더라도 공유 메모리·세마포어 같은 시스템 자원이 누수되지 않도록 정리하는 역할 |


- `--reload` 없이 실행했을때


<img width="2644" height="478" alt="Image" src="https://github.com/user-attachments/assets/c4ec0d40-3df0-4c11-acb8-869222bc02f8" />


| 컬럼 | 의미 |
|---|---|
| PID | 프로세스를 구분하는 고유 식별자 |
| TTY | 프로세스가 연결된 터미널 정보 |
| TIME | 프로세스가 사용한 CPU 누적 시간 |
| CMD | 해당 프로세스를 실행한 명령 또는 프로그램 이름 |


## 1-3. `top`
- `top -pid [pid]`
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` 로 FastAPI 실행
- `top -pid 1663 -pid 1664 -pid 1665 -pid 1666 -pid 1667 -pid 1668 -pid 1669`


<img width="2610" height="740" alt="Image" src="https://github.com/user-attachments/assets/43d77bde-0264-4d89-a73e-247595ea581a" />


<img width="2634" height="744" alt="Image" src="https://github.com/user-attachments/assets/eb6b5839-96f1-4c6d-895c-87d302035d2d" />


- 워커 프로세스 그룹이 idle 상태로 대기 중인 모습
- 관찰된 7개 프로세스는 PGRP가 모두 `1663`으로, 하나의 프로세스 그룹을 이룸
- PID 1666 ~ 1669는 각각 독립 프로세스이고, 프로세스마다 자기 인터프리터와 GIL을 갖기 때문에 워커 간에는 GIL 경쟁이 없음. 대신 워커당 메모리를 190M 씩 더 씀


| 컬럼 | 의미 |
|---|---|
| #TH | 해당 프로세스가 보유한 **스레드 수** |
| #WQ | 워크 큐(work queue) 스레드 수 |
| #POR | 열려 있는 Mach 포트 수 (소켓·IPC 채널 등) |
| MEM | 물리 메모리 사용량 (RSS) |
| CMPRS | 메모리 압박으로 **압축된** 페이지 크기 |
| PGRP | 프로세스 그룹 ID |
| PPID | 부모 프로세스 ID |
| STATE | 프로세스 상태 |

# 2. Wireshark를 이용한 HTTP(Webhook) 통신 분석
> 로컬에서 싫행한 ngrok 서버와 개인 프로젝트 FastAPI 서버의 통신 관찰

## 2-1. 관찰 환경
| 항목 | 내용 |
|---|---|
| Server | FastAPI(Uvicorn) |
| Tunnel | ngrok |
| Capture Interface | `lo0 (Loopback)` |
| Capture Filter | `tcp.port == 8000 ` |

- GitHub Webhook은 HTTPS로 ngrok 서버까지 전송됨
- ngrok가 이를 localhost의 FastAPI(8000)로 전송하므로 `lo0` 인터페이스에서 HTTP Payload까지 확인

## 2-2. 패킷 흐름

<img width="3060" height="698" alt="Image" src="https://github.com/user-attachments/assets/1dd6e25e-b75c-4916-862f-53c2977be94d" />

### TCP 연결 수립

| No | Packet | 설명 |
|-----|--------|------|
| 3 | SYN | 클라이언트(ngrok)가 FastAPI(8000)에 연결 요청 |
| 4 | SYN, ACK | 서버가 연결 요청 수락 |
| 5 | ACK | TCP 3-way Handshake 완료 |


- 초기에 한 번 `RST, ACK`가 발생했으나 이후 새로운 연결에서 정상적으로 Handshake가 수행되어 Webhook 처리에는 영향을 주지 않았다.

### HTTP POST 요청
| No | Packet | 설명 |
|-----|--------|------|
| 7~8 | POST /webhook | GitHub Webhook의 HTTP POST 요청 |

HTTP 요청은 약 22KB 크기의 JSON Payload였으며,

Wireshark에서는

```
[2 Reassembled TCP Segments]
#7 (16332 bytes)
#8 (6335 bytes)
```

로 표시되었다.

### TCP ACK

| No | Packet | 설명 |
|-----|--------|------|
| 9 | ACK | 첫 번째 데이터 수신 확인 |
| 10 | ACK | 나머지 데이터 수신 확인 |

### HTTP 응답

| No | Packet | 설명 |
|-----|--------|------|
| 11 | HTTP/1.1 200 OK | FastAPI가 Webhook 요청을 정상 처리한 후 응답 |

### TCP 연결 종료

| No | Packet | 설명 |
|-----|--------|------|
| 13 | FIN, ACK | 서버가 연결 종료 요청 |
| 14 | ACK | 클라이언트가 FIN 확인 |
| 15 | FIN, ACK | 클라이언트도 종료 요청 |
| 16 | ACK | 서버가 마지막 ACK 전송 |

- TCP 4-way Handshake를 통해 연결이 정상적으로 종료되었다.

### HTTP Payload

<img width="1662" height="808" alt="Image" src="https://github.com/user-attachments/assets/268b08f0-38a4-4bca-949b-7e3d7020f2cc" />



