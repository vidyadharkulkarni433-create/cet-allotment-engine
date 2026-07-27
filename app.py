import os
import pandas as pd
import streamlit as st
import re

st.set_page_config(page_title="MHT CET Smart Allotment Engine", page_icon="🎓", layout="wide")

st.title("🎓 MHT CET Smart Allotment Engine")
st.markdown("Upload your option list to simulate CAP Round Allotment using official state cutoffs.")

# --- SIDEBAR: CANDIDATE PROFILE ---
st.sidebar.header("Candidate Profile")
name = st.sidebar.text_input("Candidate Full Name", "")
state_rank = st.sidebar.number_input("State General Merit Rank (SML)", min_value=1, value=15000, step=1)

# Categories adjusted to match official MHT CET column names
category = st.sidebar.selectbox(
    "Category Quota",
    ["GOPENS", "EWS", "GOBCS", "GSCS", "GSTS", "GVJS", "GNT1S", "GNT2S", "GNT3S", "TFWS"]
)
category_rank = st.sidebar.number_input(f"{category} Merit Rank (Leave at 0 if OPEN/GOPENS)", min_value=0, value=0, step=1)

RAW_FILE = "cutoff mht cet 2025.xlsx"
CLEAN_FILE = "clean_master_cutoffs.csv"

@st.cache_data
def load_and_clean_data():
    # If already cleaned previously, load it instantly
    if os.path.exists(CLEAN_FILE):
        return pd.read_csv(CLEAN_FILE)
    
    # Check if the raw file is available
    if not os.path.exists(RAW_FILE):
        return None
        
    # Read the messy raw excel file
    try:
        df_raw = pd.read_excel(RAW_FILE, header=None)
    except Exception as e:
        return None
        
    clean_data = []
    current_course = None
    categories = None
    
    for index, row in df_raw.iterrows():
        row_str = " ".join([str(val) for val in row.values if pd.notna(val)])
        
        # 1. Find Course Code (e.g., '0100224210 - Computer Science')
        match = re.search(r'(\d{9,10})\s*-', row_str)
        if match:
            current_course = match.group(1)
            continue
            
        # 2. Find the row with category headers
        if current_course and 'GOPENS' in row_str and not categories:
            categories = [str(val).strip() for val in row.values if pd.notna(val) and val != 'Stage']
            continue
            
        # 3. Find the row with actual rank numbers
        if current_course and categories and 'I' in str(row.values[0]):
            ranks = [str(val).split('\n')[0].strip() for val in row.values if pd.notna(val) and str(val).strip() != 'I']
            row_dict = {'COURSE CODE': current_course}
            
            for i in range(min(len(categories), len(ranks))):
                clean_rank = re.sub(r'[^\d]', '', ranks[i])
                if clean_rank:
                    row_dict[categories[i]] = int(clean_rank)
            
            clean_data.append(row_dict)
            current_course = None
            categories = None
            
    # Save the cleaned data to CSV so it runs lightning fast next time
    clean_df = pd.DataFrame(clean_data)
    clean_df.to_csv(CLEAN_FILE, index=False)
    return clean_df

master_df = load_and_clean_data()

st.subheader("📋 Option Form Input")
uploaded_file = st.file_uploader("Upload your Option Form (Excel)", type=["xlsx", "csv"])

if uploaded_file is not None:
    if master_df is None:
        st.error(f"⚠️ Could not load '{RAW_FILE}'. Ensure it is uploaded to GitHub exactly with this name.")
    else:
        try:
            # Smart Option Form Reader
            temp_df = pd.read_excel(uploaded_file, header=None)
            header_row = temp_df[temp_df.apply(lambda row: row.astype(str).str.contains("COURSE CODE", case=False, na=False).any(), axis=1)].index

            if len(header_row) > 0:
                df = pd.read_excel(uploaded_file, skiprows=header_row[0])
            else:
                df = pd.read_excel(uploaded_file)

            st.success(f"Option form loaded! Total choices: {len(df)}")

            if st.button("🚀 Run CAP Allotment Process", type="primary"):
                allotted_row = None
                matched_pref = 0
                allotted_category_seat = ""
                final_course_code = ""

                # Cross-check student choices against Master Database
                for index, row in df.iterrows():
                    course_code_val = None
                    for col in df.columns:
                        if "course code" in str(col).lower():
                            course_code_val = str(row[col]).strip()
                            break

                    if not course_code_val:
                        continue

                    # Search in Master Cleaned Database
                    master_match = master_df[master_df["COURSE CODE"].astype(str) == course_code_val]

                    if not master_match.empty:
                        master_row = master_match.iloc[0]

                        # Check Category Cutoff First
                        if category != "GOPENS" and category_rank > 0 and category in master_df.columns:
                            cutoff_cat = pd.to_numeric(master_row[category], errors="coerce")
                            if pd.notna(cutoff_cat) and category_rank <= cutoff_cat:
                                allotted_row = row
                                matched_pref = index + 1
                                allotted_category_seat = category
                                final_course_code = course_code_val
                                break

                        # Check General (GOPENS) Cutoff
                        if "GOPENS" in master_df.columns:
                            cutoff_open = pd.to_numeric(master_row["GOPENS"], errors="coerce")
                            if pd.notna(cutoff_open) and state_rank <= cutoff_open:
                                allotted_row = row
                                matched_pref = index + 1
                                allotted_category_seat = "GOPENS"
                                final_course_code = course_code_val
                                break

                if allotted_row is not None:
                    st.balloons()
                    candidate_name = name if name else "Candidate"
                    st.success(f"🎉 Congratulations {candidate_name}! A seat has been allotted.")
                    st.subheader(f"🎯 Allotted Preference: #{matched_pref}")
                    st.info(f"Seat Allotted Under Quota: {allotted_category_seat}")

                    col_name = next((c for c in df.columns if "college name" in str(c).lower()), None)
                    crs_name = next((c for c in df.columns if "course name" in str(c).lower()), None)

                    st.markdown(f"**🏫 Institute:** {allotted_row[col_name] if col_name else 'Institute Found'}")
                    st.markdown(f"**💻 Branch:** {allotted_row[crs_name] if crs_name else 'Branch Found'}")
                    st.markdown(f"**🔢 Course Code:** {final_course_code}")
                else:
                    st.warning("⚠️ No seat allotted. Your merit rank is higher than the cutoffs for all options provided.")

        except Exception as e:
            st.error(f"Error processing the file: {e}")
