from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o")

class Grade(BaseModel):
    """관련성 확인을 위한 점수 스키마"""

    binary_score: str = Field(description="문서가 질문과 관련이 있는지 여부, 'yes' 또는 'no'")


def decide_to_generate(state):
    """
    답변을 생성할지, 아니면 질문을 다시 생성할지 결정합니다.
    """

    print("----- ASSESS GRADED DOCUMENTS -----")
    if state.get("retry_num", 0) >= 3: # [ 1 ]
        return "generate"

    grader = llm.with_structured_output(Grade) # [ 2 ]

    grader_prompt = ChatPromptTemplate.from_messages( # [ 3 ]
        [
            (
                "system",
                """
                당신은 검색된 문서가 사용자 질문과 관련이 있는지 평가하는 평가자입니다.
                문서가 사용자 질문과 관련된 키워드나 의미를 포함하고 있다면 관련성이 있다고 평가하세요.
                엄격한 테스트일 필요는 없습니다. 목표는 잘못된 검색 결과를 필터링하는 것입니다.
                문서가 질문과 관련이 있는지를 나타내는 'yes' 또는 'no'의 이진 점수를 제공하세요.
                """
            ),
            (
                "user",
                "검색된 문서: {context} \n\n 사용자 질문: {question} \n\n 관련성 점수:"
            ),
        ]
    )

    chain = grader_prompt | grader

    question = state.get("question", "")
    context = state.get("context", "")

    if not context or not question:
        print("---ERROR: Missing context or question, defaulting to generate---")
        return "generate"

    score = chain.invoke({"question": question, "context": context})
    grade = score.binary_score # [ 4 ]

    if grade == "no":
        print(
            "---DECISION: RETRIEVED DOCUMENT ARE NOT RELEVANT TO QUESTION, TRANSFORM QUERY---"
        )
        return "transform_query"
    else:
        print("---DECISION: GENERATE---")
        return "generate"



class GradeHallucinations(BaseModel):
    """생성된 답변의 환각 여부를 판단하기 위한 점수 스키마"""

    binary_score: str = Field(
        description="답변이 사실에 근거하고 있는지 여부, 'yes' 또는 'no'"
    )

def check_hallucinations(state):
    """
    생성된 답변이 문서에 근거하고 질문에 답하는지 판단합니다.
    """

    print("----- CHECK HALLUCINATIONS -----")
    question = state["question"]
    context = state["context"]
    answer = state["answer"]

    structured_llm = llm.with_structured_output(GradeHallucinations)

    system = """당신은 LLM이 생성한 답변이 검색된 사실들에 근거하고 있는지 평가하는 평가자입니다.
    'yes' 또는 'no'의 이진 점수를 제공하세요. 'yes'는 답변이 사실들에 근거하고 있음을 의미합니다."""
    hallucination_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            ("user", "질문: {question} \n\n 사실 집합: \n\n {context} \n\n LLM 생성 답변: {generation}"),
        ]
    )

    hallucination_grader = hallucination_prompt | structured_llm

    score = hallucination_grader.invoke(
        {"question": question, "context": context, "generation": answer}
    )
    grade = score.binary_score
    if grade == "yes":
        print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---")
        return "support"
    else:
        print("---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS, RE-TRY---")
        return "not supported"
