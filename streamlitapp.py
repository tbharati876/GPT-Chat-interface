%%writefile app.py
import streamlit as st
import pandas as pd
import re

@st.cache_data
def load_data():
    project = pd.read_csv("project.csv")
    address = pd.read_csv("ProjectAddress.csv")
    config = pd.read_csv("ProjectConfiguration.csv")
    variant = pd.read_csv("ProjectConfigurationVariant.csv")
    return project, address, config, variant

project, address, config, variant = load_data()

def parse_query(query):
    city, bhk, budget = None, None, None

    bhk_match = re.search(r'(\\d)\\s*bhk', query, re.I)
    if bhk_match: bhk = int(bhk_match.group(1))

    budget_match = re.search(r'₹?\\s*([\\d\\.]+)\\s*(cr|crore|l|lakh)?', query, re.I)
    if budget_match:
        val = float(budget_match.group(1))
        unit = budget_match.group(2)
        if unit and 'l' in unit.lower():
            budget = val * 1e5
        elif unit and 'cr' in unit.lower():
            budget = val * 1e7
        else:
            budget = val

    cities = ['Pune','Mumbai','Bangalore','Hyderabad','Delhi','Chennai']
    for c in cities:
        if c.lower() in query.lower():
            city = c
            break
    return {"city": city, "bhk": bhk, "budget": budget}

def search_projects(filters):
    df = project.copy()
    if filters["city"]:
        df = df[df["City"].astype(str).str.contains(filters["city"], case=False, na=False)]
    if filters["bhk"]:
        df = df[df["Configuration"].astype(str).str.contains(str(filters["bhk"]), na=False)]
    if filters["budget"]:
        df = df[df["Price"] <= filters["budget"]]
    return df

def generate_summary(df, filters):
    if df.empty:
        return f"No {filters['bhk']}BHK options found under ₹{(filters['budget'] or 0)/1e7:.1f} Cr in {filters['city']}."
    avg_price = df["Price"].mean()/1e7
    locs = ", ".join(df["Locality"].dropna().unique()[:3])
    return f"Found {len(df)} matching {filters['bhk']} BHK homes in {filters['city']}. " \
           f"Average price ≈ ₹{avg_price:.1f} Cr. Popular areas: {locs}."

# --- Streamlit UI ---
st.set_page_config(page_title="NoBrokerage Chatbot", page_icon="🏠", layout="centered")

st.title(" NoBrokerage Property Chatbot")
st.write("Ask in plain language, e.g. *3BHK flat in Pune under ₹1.2 Cr*")

user_query = st.text_input("Your query:")

if user_query:
    filters = parse_query(user_query)
    results = search_projects(filters)
    summary = generate_summary(results, filters)
    st.markdown("###  Summary")
    st.write(summary)
    st.markdown("###  Matching Properties")
    if results.empty:
        st.warning("No results found.")
    else:
        st.dataframe(results[["ProjectName","City","Locality","Configuration","Price","PossessionStatus"]].head(10))
