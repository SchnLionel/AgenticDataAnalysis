import streamlit as st
import json
from frontend.utils.api_client import APIClient

st.title("Data Analysis Chat")

client = APIClient()

if "access_token" not in st.session_state:
    st.warning("Please login first.")
    st.stop()

# Sidebar: Session Management
with st.sidebar:
    st.subheader("Analysis Sessions")
    
    if st.button("➕ New Session"):
        st.session_state.show_new_session_form = True

    if st.session_state.get("show_new_session_form"):
        with st.form("new_session_form"):
            title = st.text_input("Session Title", value="New Analysis")
            datasets = client.list_datasets()
            ds_names = {f"{ds['filename']} (ID: {ds['id']})": ds['id'] for ds in datasets}
            selected_ds = st.selectbox("Select Dataset", options=["None"] + list(ds_names.keys()))
            
            if st.form_submit_button("Create"):
                ds_id = ds_names[selected_ds] if selected_ds != "None" else None
                new_session = client.create_session(title, ds_id)
                if new_session:
                    st.session_state.current_session_id = new_session["id"]
                    st.session_state.show_new_session_form = False
                    st.success(f"Session '{title}' created!")
                    st.rerun()
                else:
                    st.error("Failed to create session.")

    st.divider()
    
    # Load past sessions
    sessions = client.get_sessions()
    for session in sessions:
        if st.button(f"📁 {session['title']}", key=f"session_{session['id']}"):
            st.session_state.current_session_id = session["id"]
            st.rerun()

# Main area: Chat Interface
if "current_session_id" in st.session_state:
    session_id = st.session_state.current_session_id
    
    # Load session detail (with history)
    session_detail = client.get_session_detail(session_id)
    if not session_detail:
        st.error("Could not load session.")
        st.stop()
    
    st.info(f"**Session:** {session_detail['title']} | **Dataset:** {session_detail['dataset_id'] if session_detail['dataset_id'] else 'None'}")

    # Display chat history
    for message in session_detail["messages"]:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            # Display visualizations
            if message.get("visualizations"):
                for viz in message["visualizations"]:
                    st.plotly_chart(viz["figure_json"], use_container_width=True)

    # Chat input
    if prompt := st.chat_input("Ask about your data..."):
        # Display user message immediately
        with st.chat_message("user"):
            st.write(prompt)
            
        # Call Backend Agent
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                res = client.query_agent(session_id, prompt)
                if "error" in res:
                    st.error(f"Error: {res['error']}")
                else:
                    st.write(res["synthesis"])
                    # Display new figures
                    if res.get("figures"):
                        for fig_json in res["figures"]:
                            # fig_json is already a dict from json.loads in agent_manager
                            st.plotly_chart(fig_json, use_container_width=True)
                    st.rerun() # Refresh to show persisted history correctly
else:
    st.info("👈 Select a session from the sidebar or create a new one.")
