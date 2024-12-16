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
    previous_conversation_state,
    last_user_message,
    last_assistant_message,
):
    prompt = f"""
You are a conversation history summarizer with state awareness. Your task is to maintain both an ongoing summary of the conversation and track the current conversational context.

Current Summary: {previous_summarized_history}
Current State: {previous_conversation_state}
New Message: {last_user_message}
Response: {last_assistant_message}

STATE TRACKING GUIDELINES:
1. Monitor for any contextual shifts in the conversation that change how future messages should be interpreted
2. State changes can include but are not limited to:
   - Changes in conversation purpose or direction
   - New constraints or requirements
   - Context switches
   - Special handling requests
3. Maintain current state until a clear contextual shift occurs
4. State should inform how new information is processed and summarized

SUMMARY GUIDELINES:
1. If this is the first message (current_summary is empty), create an initial summary
2. If there's an existing summary, integrate the new information while:
   - Preserving essential context from previous messages
   - Removing redundant information
   - Maintaining chronological flow
   - Keeping focus on actionable items and key decisions
3. Include:
   - Current conversational state/context
   - Main topics discussed
   - Decisions made
   - Action items or next steps
   - Important context shifts
4. Exclude:
   - Pleasantries and small talk
   - Redundant information
   - Minor clarifications
5. Format the summary in past tense
6. Keep the summary concise (maximum 200 words)

Output Format:
{{
    "summarized_history": string,
    "conversation_state": string
}}
"""

    response = client.chat.completions.create(
        model=st.session_state["openai_model"],
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    response = response.choices[0].message.content
    if response is None:
        raise Exception("OpenAI API response is None")

    # decode json
    response = json.loads(response)
    _summarized_history = response["summarized_history"]
    _conversation_state = response["conversation_state"]
    return _summarized_history, _conversation_state


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

[Conversation State]
{st.session_state.conversation_state}

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
    st.session_state.summarized_history, st.session_state.conversation_state = (
        get_history(
            st.session_state.summarized_history,
            st.session_state.conversation_state,
            prompt,
            response,
        )
    )

st.markdown(
    f"""
            **Summary**
            {st.session_state.summarized_history}

            **Conversation State**
            {st.session_state.conversation_state}
            """
)
