import streamlit as st
import google.generativeai as genai
import json
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="IIMN Interview Debrief", page_icon="🎙️")

# --- SIDEBAR: CONFIGURATION ---
st.sidebar.header("Configuration")
# For the deployed version, put this in st.secrets to hide it from students
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# --- MAIN UI ---
st.title("🎙️ IIMN Interview Voice Collector")
st.markdown("""
**Don't type. Just speak.**
Record your interview experience while it's fresh. We will structure it for the batch database.
""")

# --- INPUT METHOD ---
tab1, tab2 = st.tabs(["🔴 Record Voice", "📂 Upload Audio"])

audio_file = None

with tab1:
    # New Streamlit Audio Recorder
    recorded_audio = st.audio_input("Click to Record")
    if recorded_audio:
        audio_file = recorded_audio

with tab2:
    uploaded_file = st.file_uploader("Upload WhatsApp/Voice Note", type=["mp3", "wav", "m4a", "ogg"])
    if uploaded_file:
        audio_file = uploaded_file

# --- THE LOGIC ---
if audio_file and st.button("Process Experience"):
    if not api_key:
        st.error("⚠️ API Key is missing.")
    else:
        try:
            with st.spinner("Listening and extracting data..."):
                # 1. Configure Gemini
                genai.configure(api_key=api_key)
                
                # 2. Use Flash (Essential for Audio Processing)
                # We force 'gemini-1.5-flash' because 'pro' cannot hear audio.
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                # 3. Read the audio bytes
                audio_bytes = audio_file.read()
                
                # 4. The Prompt (Mapped strictly to your PDF fields)
                prompt = """
                Role: Data Extraction Specialist for IIM Nagpur Placement Committee.
                Task: Listen to this student's interview experience and extract structured data.
                
                Target Schema (JSON):
                {
                    "Candidate_Name": "Extract if mentioned, else 'Anonymous'",
                    "Company": "Name of the company",
                    "Role_Offered": "Job role/profile",
                    "Round_Type": "Technical / HR / Case / GD",
                    "Questions_Asked": ["List of specific questions asked..."],
                    "Preparation_Tips": "Advice given by the student",
                    "Work_Ex_Duration": "Mentioned work ex in months (if any)"
                }
                
                Instructions:
                1. If the student speaks in Hinglish, translate to professional English.
                2. Extract as many specific questions as possible.
                3. Return ONLY the JSON object.
                """
                
                # 5. Generate Content (Multimodal: Audio + Text)
                response = model.generate_content([
                    prompt,
                    {"mime_type": "audio/mp3", "data": audio_bytes}
                ])
                
                # 6. Parse JSON
                try:
                    # Clean up JSON string (remove markdown ```json ... ```)
                    json_str = response.text.replace("```json", "").replace("```", "").strip()
                    data = json.loads(json_str)
                    
                    # --- DISPLAY RESULTS ---
                    st.success("✅ Data Extracted Successfully!")
                    
                    # Display as key-value pairs
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Company", data.get("Company", "N/A"))
                        st.metric("Role", data.get("Role_Offered", "N/A"))
                    with col2:
                        st.metric("Round Type", data.get("Round_Type", "N/A"))
                    
                    st.subheader("📝 Questions Asked")
                    for q in data.get("Questions_Asked", []):
                        st.write(f"- {q}")
                        
                    st.subheader("💡 Prep Tips")
                    st.info(data.get("Preparation_Tips", "No specific tips provided."))
                    
                    # --- DOWNLOAD BUTTON ---
                    # Convert to DataFrame for CSV download
                    df = pd.DataFrame([data])
                    csv = df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download as CSV (For Database)",
                        data=csv,
                        file_name=f"{data.get('Company')}_Interview_Data.csv",
                        mime="text/csv",
                    )
                    
                except json.JSONDecodeError:
                    st.error("Error parsing the AI response. Here is the raw text:")
                    st.write(response.text)
                    
        except Exception as e:
            st.error(f"An error occurred: {e}")

st.markdown("---")
st.caption("IIM Nagpur Prep Comm • Voice-to-Data Initiative")
