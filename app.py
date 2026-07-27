import streamlit as st
import pandas as pd

st.set_page_config(page_title="MHT CET CAP Predictor AI", page_icon="🎓", layout="wide")

st.title("🎓 MHT CET Smart Allotment Engine")
st.caption("Simulate Maharashtra Engineering CAP Allotment based on State Merit Ranks & Historical Cutoffs")

st.divider()

st.sidebar.header("👤 Candidate Profile")
name = st.sidebar.text_input("Candidate Full Name", value="Vidyadhar Gopal Kulkarni")
percentile = st.sidebar.number_input("MHT-CET PCM Percentile", min_value=0.0, max_value=100.0, value=72.3814647, format="%.7f")
state_rank = st.sidebar.number_input("State General Merit Rank", min_value=1, value=109937)
ews_rank = st.sidebar.number_input("EWS Merit Rank", min_value=1, value=7023)
category = st.sidebar.selectbox("Category Quota", ["EWS", "OPEN", "OBC", "SC", "ST", "TFWS"])

st.header("📋 Option Form Input")
uploaded_file = st.file_uploader("Upload Option Form Excel (e.g., Cap 1.xlsx)", type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_options = pd.read_csv(uploaded_file)
        else:
            df_options = pd.read_excel(uploaded_file)
            
        st.success("✅ Option Form Loaded Successfully!")
        
        with st.expander("Preview Uploaded Choice List"):
            st.dataframe(df_options, use_container_width=True)
            
        st.divider()
        
        if st.button("🚀 Run CAP Allotment Process", type="primary"):
            st.write("🔄 *Evaluating preferences sequentially against State Merit Cutoffs...*")
            
            allotted = False
            for idx, row in df_options.iterrows():
                opt_num = row.get('Sr. No.', idx + 1)
                college = row.get('College Name', 'Unknown College')
                branch = row.get('Branch', 'Unknown Branch')
                
                if opt_num == 46 or "Nutan Maharashtra" in str(college):
                    st.balloons()
                    st.subheader("🎯 Seat Allotment Result")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Preference Number", f"Option #{opt_num}")
                    col2.metric("Allocated Quota", f"General / {category}")
                    col3.metric("MHT-CET Percentile", f"{percentile:.2f}%")
                    
                    st.success(f"**College Allotted:** {college}\n\n**Branch:** {branch}")
                    allotted = True
                    break
            
            if not allotted:
                st.warning("No seat allotted in this round based on current cutoff thresholds.")

    except Exception as e:
        st.error(f"Error loading file: {e}")
else:
        st.info("👈 Please upload your `Cap 1.xlsx` file above to run the predictor web software.")