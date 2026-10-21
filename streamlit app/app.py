import streamlit as st

pages = [
    st.Page("Pages/Home.py", title="Home"),
    st.Page("Pages/First_month.py", title="First Month"),
    st.Page("Pages/analysis.py", title="Analysis"),
    st.Page("Pages/test.py", title="Test"),
<<<<<<< HEAD
]

pg = st.navigation(pages)

pg.run()
=======
    st.Page(
        "Pages/Cross_border_flows.py",
        title="Cross-border flows"
    ),
]

pg = st.navigation(pages)
pg.run()




>>>>>>> Assignment-2-branch
