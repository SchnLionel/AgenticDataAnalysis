import streamlit as st
from frontend.utils.api_client import APIClient

st.set_page_config(layout="wide", page_title="DataStream AI", page_icon="📊")

if "access_token" not in st.session_state:
    st.title("Welcome to DataStream AI")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    client = APIClient()
    
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            res = client.login(email, password)
            if "access_token" in res:
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(f"Login failed: {res.get('error', 'Unknown error')}")
                
    with tab2:
        new_email = st.text_input("Email", key="reg_email")
        new_password = st.text_input("Password", type="password", key="reg_password")
        if st.button("Register"):
            res = client.register(new_email, new_password)
            if "id" in res:
                st.success("Registered successfully! Please login.")
            else:
                st.error(f"Registration failed: {res.get('error', 'Unknown error')}")
else:
    # Authenticated State
    st.sidebar.title("DataStream AI")
    if st.sidebar.button("Logout"):
        client = APIClient()
        client.logout()
        st.rerun()

    # Navigation
    st.title("Main Dashboard")
    st.write(f"Logged in as session user.")
    
    st.info("👈 Use the sidebar to navitage to the Analysis page.")
    
    # We can use st.Page for a better navigation if we อยาก
    analysis_page = st.Page("frontend/pages/analysis.py", title="Data Analysis", icon="📈")
    dataset_page = st.Page("frontend/pages/datasets.py", title="My Datasets", icon="📁")
    
    pg = st.navigation([analysis_page, dataset_page])
    pg.run()
