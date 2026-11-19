
import streamlit as st
from pathlib import Path
import tempfile
import json

from mini_project import (
    parse_job_description,
    read_resume,
    parse_resume,
    final_score
)

st.set_page_config(
    page_title="ResumeIQ",
    page_icon="📄",
    layout="wide"
)

# custom css
st.markdown("""
<style>

.stApp {
    background: #090D18;
    color: #E5E7EB;
}

header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: #0D1423;
    border-right: 1px solid #1E293B;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
}

.main-title {
    font-size: 42px;
    font-weight: 800;
    color: #FFFFFF;
}

.main-title span {
    color: #00E5FF;
}

.sub-title {
    color: #94A3B8;
    font-size: 15px;
}

.section-title {
    color: #00E5FF;
    font-size: 21px;
    font-weight: 700;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #101B2D;
    border: 1px solid #263750;
    border-radius: 14px;
}

.stTextArea textarea {
    background: #0D1728;
    color: #FFFFFF;
    border: 1px solid #334155;
    border-radius: 10px;
}

.stTextArea textarea:focus {
    border: 1px solid #00E5FF;
    box-shadow: 0 0 8px #00E5FF55;
}

[data-testid="stFileUploader"] {
    background: #0D1728;
    border: 1px dashed #00B8D4;
    border-radius: 12px;
    padding: 12px;
}

div.stButton > button {
    background: linear-gradient(90deg, #0066FF, #00C8FF);
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    height: 48px;
    font-weight: 700;
}

div.stButton > button:hover {
    background: linear-gradient(90deg, #0052CC, #00A6D6);
    color: white;
    box-shadow: 0 0 15px #00C8FF66;
}

[data-testid="stMetric"] {
    background: #101B2D;
    border: 1px solid #263750;
    border-radius: 12px;
    padding: 16px;
}

[data-testid="stMetricValue"] {
    color: #00E5FF;
}

.stTabs [data-baseweb="tab"] {
    color: #94A3B8;
}

.stTabs [aria-selected="true"] {
    color: #00E5FF !important;
}

.stProgress > div > div > div > div {
    background-color: #00E5FF;
}

hr {
    border-color: #263750;
}

</style>
""", unsafe_allow_html=True)


# sidebar
with st.sidebar:

    st.markdown(
        "<h2 style='color:#00E5FF;'>RESUME<span style='color:white;'>IQ</span></h2>",
        unsafe_allow_html=True
    )

    st.caption("AI Resume Intelligence")

    st.divider()

    st.markdown("### Workspace")

    st.write("📄 Resume Analyzer")
    st.write("📊 Candidate Analysis")

    st.divider()

    st.markdown("### Features")

    st.write("✦ Resume Parsing")
    st.write("✦ Skills Extraction")
    st.write("✦ Job Matching")
    st.write("✦ AI Scoring")

    st.divider()

    st.caption("POWERED BY GROQ AI")


# main heading
st.markdown(
    '<div class="main-title">Resume<span>IQ</span></div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-title">AI-powered resume screening and job matching platform.</div>',
    unsafe_allow_html=True
)

st.write("")
st.divider()


# input section
st.markdown(
    '<div class="section-title">01 / Job Description</div>',
    unsafe_allow_html=True
)

st.write("Paste the job requirements you want to match.")

job_description = st.text_area(
    "Job Description",
    height=200,
    placeholder="Enter job title, responsibilities, required skills...",
    label_visibility="collapsed"
)

st.write("")

st.markdown(
    '<div class="section-title">02 / Upload Resume</div>',
    unsafe_allow_html=True
)

uploaded_file = st.file_uploader(
    "Upload PDF or DOCX",
    type=["pdf", "docx"]
)

if uploaded_file is not None:
    st.success("Uploaded: " + uploaded_file.name)

st.write("")

analyze_button = st.button(
    "⚡ Analyze Resume",
    use_container_width=True
)


# analysis
if analyze_button:

    if not job_description.strip():
        st.warning("Please enter a Job Description.")

    elif uploaded_file is None:
        st.warning("Please upload your resume.")

    else:

        temp_path = None

        try:

            with st.spinner("AI is analyzing your resume..."):

                # save uploaded file
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=Path(uploaded_file.name).suffix
                ) as temp_file:

                    temp_file.write(uploaded_file.getvalue())
                    temp_path = Path(temp_file.name)

                # read resume
                resume_text = read_resume(temp_path)

                if not resume_text or not resume_text.strip():

                    st.error("Could not extract text from resume.")

                else:

                    # analyze job and resume
                    job = parse_job_description(job_description)
                    resume = parse_resume(resume_text)
                    result = final_score(job, resume)

                    score = max(0, min(100, float(result.score)))

                    st.success("Analysis completed successfully!")

                    st.divider()

                    # candidate details
                    st.markdown(
                        '<div class="section-title">03 / Candidate Profile</div>',
                        unsafe_allow_html=True
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Candidate", resume.name or "N/A")

                    with col2:
                        st.metric("Email", resume.email or "N/A")

                    with col3:
                        st.metric("Phone", resume.phone or "N/A")

                    st.write("")

                    # score
                    st.markdown(
                        '<div class="section-title">04 / Match Score</div>',
                        unsafe_allow_html=True
                    )

                    with st.container(border=True):

                        st.caption("OVERALL JOB MATCH")

                        st.markdown(
                            f"""
                            <h1 style="
                                color:#00E5FF;
                                font-size:55px;
                                margin:0;
                            ">{score:.1f}%</h1>
                            <p style="color:#94A3B8;">
                                Resume compatibility score
                            </p>
                            """,
                            unsafe_allow_html=True
                        )

                        st.progress(int(score))

                    st.write("")

                    # quick stats
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Experience",
                            f"{resume.total_experience} Years"
                            if resume.total_experience is not None
                            else "N/A"
                        )

                    with col2:
                        st.metric("Skills", len(resume.skills))

                    with col3:
                        st.metric("Projects", len(resume.projects))

                    st.divider()

                    # resume details
                    st.markdown(
                        '<div class="section-title">05 / Resume Details</div>',
                        unsafe_allow_html=True
                    )

                    tab1, tab2, tab3, tab4 = st.tabs([
                        "Skills",
                        "Education",
                        "Experience",
                        "Projects"
                    ])

                    with tab1:

                        st.subheader("Technical Skills")
                        st.write(resume.skills)

                        st.subheader("Certifications")
                        st.write(resume.certifications)

                    with tab2:

                        st.subheader("Education")
                        st.write(resume.education)

                    with tab3:

                        st.subheader("Work Experience")

                        for experience in resume.experiences:

                            with st.expander(
                                experience.role or "Experience"
                            ):

                                st.write("Company:", experience.company)
                                st.write("Duration:", experience.duration)
                                st.write("Description:", experience.description)
                                st.write("Skills:", experience.skill_used)

                    with tab4:

                        st.subheader("Projects")
                        st.write(resume.projects)

                    st.divider()

                    # ai feedback
                    st.markdown(
                        '<div class="section-title">06 / AI Evaluation</div>',
                        unsafe_allow_html=True
                    )

                    with st.expander("View AI Analysis", expanded=True):
                        st.json(result.details)

                    # download report
                    report = {
                        "candidate": resume.model_dump(),
                        "score": result.score,
                        "details": result.details
                    }

                    st.download_button(
                        "Download Analysis Report",
                        data=json.dumps(report, indent=4),
                        file_name="resume_report.json",
                        mime="application/json"
                    )

        except Exception as error:

            st.error("Something went wrong!")
            st.exception(error)

        finally:

            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
