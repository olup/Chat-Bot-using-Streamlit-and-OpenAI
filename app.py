from openai import OpenAI
import streamlit as st
import json

st.title("ChatGPT-like clone")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "summarized_history" not in st.session_state:
    st.session_state.summarized_history = ""

if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = ""


def get_history(
    previous_summarized_history,
    last_user_message,
    last_assistant_message,
):
    prompt = f"""
You are a conversation history summarizer. Your task is to maintain an ongoing summary that captures both content and context.

Current Summary: {previous_summarized_history}
last user message: {last_user_message}
last assistant response: {last_assistant_message}

SUMMARY GUIDELINES:
1. If this is the first message (current_summary is empty), create an initial summary
2. If there's an existing summary, integrate the new information while:
   - Preserving essential context from previous messages
   - Removing redundant information
   - Maintaining chronological flow
   - Tracking shifts in conversation purpose or direction
3. Include:
   - Main topics and their progression
   - Key decisions and their rationale
   - Current direction or focus
   - Important constraints or special handling requirements
   - Action items or next steps
4. Exclude:
   - Pleasantries and small talk
   - Redundant information
   - Minor clarifications
5. Format the summary in past tense
6. Keep the summary concise (maximum 200 words)

Updated Summary:
"""

    response = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    response = response.choices[0].message.content
    return response


if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"

if "messages" not in st.session_state:
    st.session_state.messages = []


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        previous_llm_message = (
            st.session_state.messages[-2]["content"]
            if len(st.session_state.messages) > 1
            else ""
        )
        llmPrompt = f"""
We are in a middle of a conversation.

[Summarized History]
{st.session_state.summarized_history}

[latest message from the assistant]
{previous_llm_message}

[latest message from the user]
{prompt}
"""
        print(llmPrompt)

        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {
                    "role": "user",
                    "content": llmPrompt,
                },
            ],
            stream=True,
        )
        response = st.write_stream(stream)

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.session_state.summarized_history = get_history(
        st.session_state.summarized_history,
        prompt,
        response,
    )

st.markdown(
    f"""
            **Summary**
            {st.session_state.summarized_history}
            """
)
