-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;  -- [ 1 ]


-- 2. documents 테이블 생성
CREATE TABLE documents (  -- [ 2 ]
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    storage_ref TEXT,
    filename TEXT,
    chunk_index INT DEFAULT 0,
    document_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- 3. 벡터 검색 인덱스 (코사인 유사도)
CREATE INDEX documents_embedding_idx ON documents -- [ 3 ]
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);


-- 4. 벡터 검색 RPC 함수
CREATE OR REPLACE FUNCTION match_documents( -- [ 4 ]
    query_embedding VECTOR(1536),
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    filename TEXT,
    storage_ref TEXT,
    chunk_index INT,
    document_type TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.content,
        d.filename,
        d.storage_ref,
        d.chunk_index,
        d.document_type,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
