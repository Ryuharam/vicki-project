## 공개 가중치 모델을 vLLM으로 서빙해 보기

### 개요
vLLM으로 공개 가중치 모델을 서빙해보는 실습을 하며 

ollama로 서빙을 하는 것과 vLLM으로 서빙을 하는 것을 비교해 보고 싶었다. 

colab A100에서 진행하였고, 로컬에서 FastAPI를 통해 벤치마크 테스트를 진행하였다.

### 1. Ollama + Ngrok

(코랩 링크)[https://colab.research.google.com/drive/1CdCdu2B_h2xFIFenB_X8LkI9Sh_TbgvZ?usp=sharing]

### 2. vLLM + Ngrok

(코랩 링크)[https://colab.research.google.com/drive/1JDpAe-oT-psChXpQmOQlhl5HzC63WGHi?usp=sharing]

### 3. 결과 비교
<img width="618" height="703" alt="Image" src="https://github.com/user-attachments/assets/2ebe5aca-9395-419b-82aa-554d9a3722d1" />

| 컬럼 | 단위 | 의미 |
|-----|-----|-----|
|ttft_ms_*| ms | 첫 토큰까지의 시간 |
|total_ms_*| ms | 요청 전체 시간 |
|tpot_ms_mean| ms/토큰 | 토큰 하나 생성 시간 |
|output_tps_mean| 토큰/sec | 요청 1건 기준 평균 속도 |
|agg_output_tps | 토큰/sec | 배치 전체 합산 속도 |
|throughput_req_s | 요청/sec | 초당 완료 요청 수 |

1. `output_tps_mean`과 `agg_output_tps`
`output_tps_mean`은 사용자 1명이 체감하는 속도로 동시 사용자가 늘면 내 응답도 느려지므로 떨어진다.

이때, ollama는 동시성이 1에서 16으로 증가하면 51.7 -> 11.1 (↓78%) 떨어지지만

vllm은 61.1 -> 55.6 (↓9%) 로 훨씬 더 적게 떨어지는 것을 확인할 수 있었다.

`agg_output_tps`는 서버가 초당 만들어내는 총 토큰으로 동시 요청이 늘어나면 GPU를 더 채워 증가한다.

이때, ollama는 동시성이 1에서 16으로 증가하면 53.3 -> 146.4 (2.7배) 로 증가하지만

vllm은 63.1 -> 710.2 (11배)로 훨씬 증가함을 확인할 수 있었다.

2. `tpot_ms_mean` 과 `total_ms_p50`
`topt_ms_mean` 을 보면 ollama는 14.24 -> 80.34 로 증가하는 모습을 보이지만

vllm은 13.35 -> 14.53 으로 크게 증가하지 않는 모습을 볼 수 있었다.

`total_ms_p50` 을 보면 ollama는 4508.09 -> 21994.17 로 크게 증가하는 모습을 보이지만

vllm은 3846.12 -> 2830.73 로 오히려 줄기도 했다.

### 배운점
이번 실습을 진행해보며 vllm을 띄우는 법에 대해 배울 수 있었다.

ollama와 vllm의 성능을 비교해보며 vllm의 동시 요청 처리 성능을 다시 한 번 느낄 수 있었다.

