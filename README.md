Project Overview

This project was developed as part of the IND320 course. The objective is to collect, process, store and visualize energy-related data using different data technologies, APIs and database solutions.

The project focuses on Norwegian reservoir statistics and cross-border electricity flows. The collected data is processed, stored and presented through an interactive Streamlit web application.

Features

Reservoir Statistics: Retrieve and visualize Norwegian reservoir data from the NVE Magasinstatistikk API.

Cross-border Electricity Flows: Collect electricity flow data between Norway and neighboring countries using the ENTSO-E API.

Data Processing: Process and transform energy data using Python, Pandas and PySpark.

Database Storage: Store and retrieve data using MongoDB Atlas.

Interactive Dashboard: Explore energy data through interactive visualizations and filters using Streamlit.

Data Analysis: Perform additional analysis using Jupyter Notebooks.

Project Structure

IND320-OLEGRO99/
│
├── hadoop-3.3.1/      # Hadoop installation
├── Notebooks/         # Jupyter notebooks and data analysis
├── streamlit app/     # Streamlit dashboard
│   ├── app.py
│   └── Pages/
│
├── requirements.txt   # Python dependencies
├── .gitignore
└── README.md