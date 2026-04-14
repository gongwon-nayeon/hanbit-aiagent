# 테스트 문서 인덱싱
from agent import index_document

# 테스트 문서 1개 추가
result = index_document(
    content="테스트 휴가 규정입니다. 연차휴가는 1년 근속시 15일이 부여됩니다. 경조사 휴가는 결혼 5일, 출산 10일입니다.",
    filename="휴가규정.txt",
    storage_ref="gdrive://file/test123",
    metadata={"document_type": "policy"}
)
print(result)
