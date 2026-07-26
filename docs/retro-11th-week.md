# 11주차 회고


## 좋았던점
배포와 cicd를 성공한 것이 좋았다.

## 배운점
1. 단위 테스트를 위해서 llm, vectorstore 등을 전역에서 만들고 쓰는 구조가 아니라 직접 넣어주는 방식을 택해야 한다는 것을 알게되었다.
2. EC2에 도커를 설치할 때, 원래는 cicd.yml에서 도커 설치 유무를 판단하고 설치를 진행했는데,

생각해보니 인스턴스를 처음 시작할때 설치를 진행하는 것이 좋을 것 같았다.

그래서 user data를 이용해 스크립트로 도커 설치와 초기 설정을 진행하도록 했다.

```shell
#!/bin/bash -xe
mkdir -p /var/log
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

export DEBIAN_FRONTEND=noninteractive

timedatectl set-timezone Asia/Seoul

export LANG=ko_KR.UTF-8
export LC_MESSAGES=POSIX

apt-get update -y
apt-get -o Dpkg::Options::="--force-confold" upgrade -y

apt-get install -y language-pack-ko
locale-gen ko_KR.UTF-8
update-locale LANG=ko_KR.UTF-8 LC_MESSAGES=POSIX

apt update
apt install ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

tee /etc/apt/sources.list.d/docker.sources <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

apt update
apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

usermod -aG docker ubuntu

systemctl enable docker
systemctl start docker
systemctl status docker
```

## 부족했던점
1. 단위 테스트 코드를 작성하는 방법과 테스트를 위한 리팩토링 과정을 클로드의 도움을 받아서 진행했다. 

그 과정에서 LLM 모델 fallback 이라던가 테스트 코드 작성법은 아직 다 이해하지 못한게 아쉽다. 

계속 읽어보고 흐름을 생각해보며 익혀야 겠다.

2. 배포 과정에서 pem 키를 누락한다던지 환경변수를 로컬은 바꿨는데 배포 환경은 바꾸지 않아서 문제가 생긴다던지,

배포 환경의 경로와 로컬 환경의 경로가 달라 에러가 많이 발생하고 있다. 

앞으로 더 꼼꼼히 체크를 하거나 좀 더 안정적인 방향으로 발전해야 할 것 같다.
