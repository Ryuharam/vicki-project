# 9주차 회고

## 좋았던 점
- 1차 MVP인 파이썬 코드 리뷰 게시까지 구현했다.


## 배운 점
- GitHub APP Webhook 검증 방법 (hmac, compare_digest 등)
- GitHub APP webhook 받는 방법, REST API 요청 보내고 받아오는 방법, ngrok 사용방법 

## 부족했던 점
- 응답 구조화 중 발생한 문제

    comment 결과가 매 요청마다 달라질 문제를 해결하기 위해 structured output을 적용하려고 하는데,

    gemma4:e2b-mlx 는 response_format을 잘 따르지 않고, 그로 인헤 Pydantic 검증에 통과하지 못하는 문제가 발생했다. 

    structured output이 없으면 그냥 마지막 AIMessage 를 출력하게 했으나 구조를 일치시키기 위해 프롬프트를 강화해야겠다.
- llm 모델 변경 시 에러가 나는 문제

    비용을 아끼고자 Ollama로 gemma4:e2b-mlx 모델을 쓰고 있었는데,

    gemini 로 바꾸려고 하니 에러가 발생했다. 원인을 파악하고 해결해야겠다.

    -> 모델을 변경하여 생기는 문제가 아니라 
    
    app/core/vectordb.py의 `get_vectorstore` 메서드에서 
    
    매번 PersistentClient를 생성 후 반환하여 생기는 문제였다. 

    한 번만 생성하여 반환하는 코드로 수정하였다. 

- 코드 리뷰 품질 문제
  
    pr comment를 만들고 게시는 하는데 그 코드 리뷰가 좋은 품질은 아닌 것 같다. 

    llm 을 바꾸거나 모델 파인튜닝을 이용해 리뷰 품질을 올릴 수 있는 방법을 찾아봐야 겠다.

## 바라는 점
- 파이썬 코드 리뷰 외에도 문서 코드 리뷰, 보안 확인 등의 기능에 특화된 여러 에이전트를 만들고 라우팅 해보고 싶다.
- pr 내용에 따라 merge approve, reject 등을 판단하는 노드를 추가하고 싶다.
- llm 이 달라지더라도 문제가 없도록 코드를 개선하고 싶다.
