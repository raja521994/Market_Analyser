import streamlit as st
from agent import run_agent
from langchain_core.messages import HumanMessage, AIMessage

st.set_page_config(
    page_title="Indian Equity Research Advisor",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Indian Equity Investment & Research Advisor")
st.caption("Local AI Agent • Powered by Qwen2.5-7B • Evidence-based analysis")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about any Indian stock (e.g. Analyze RELIANCE, Compare TCS vs INFY, What is ROCE?)"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing... (this may take 20-60 seconds on CPU)"):
            # Convert history for the agent
            chat_history = []
            for msg in st.session_state.messages[:-1]:
                if msg["role"] == "user":
                    chat_history.append(HumanMessage(content=msg["content"]))
                else:
                    chat_history.append(AIMessage(content=msg["content"]))
            
            response = run_agent(prompt, chat_history)
            st.markdown(response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar
with st.sidebar:
    st.header("About")
    st.write("""
    This is a **local** AI agent specialized in Indian equity research.
    
    It follows a strict analytical framework and uses real data tools.
    """)
    
    st.divider()
    st.subheader("Example Questions")
    st.code("Analyze RELIANCE")
    st.code("Compare TCS and INFY")
    st.code("What is the current valuation of HDFCBANK?")
    st.code("Explain ROCE with example")
    st.code("Should I buy SBIN for long term?")
    
    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()