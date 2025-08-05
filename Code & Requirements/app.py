import os
import pandas as pd
import streamlit as st
from gpt4all import GPT4All

# ✅ Set your local model path
MODEL_PATH = "C:/Users/Shaik Rehman/Desktop/micro_saas_app/models/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

@st.cache_resource
def load_model():
    if not os.path.exists(MODEL_PATH):
        st.error(f"Model file not found at: {MODEL_PATH}")
        st.stop()
    return GPT4All(MODEL_PATH, allow_download=False)

model = load_model()

st.set_page_config(page_title="Local Excel Bot", layout="centered")
st.title("🤖 Chat with Your Excel Data (Offline LLM)")

uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("📊 Excel Data Preview")
    st.dataframe(df.head())

    # ✅ Auto-detect your columns
    def auto_detect_columns(df):
        col_map = {
            "product_category": None,
            "quantity": None,
            "price_per_unit": None,
            "total_amount": None,
            "date": None,
            "region": None
        }
        for col in df.columns:
            lower = col.lower()
            if "product" in lower and "category" in lower:
                col_map["product_category"] = col
            elif "quantity" in lower or "qty" in lower:
                col_map["quantity"] = col
            elif "price" in lower and "unit" in lower:
                col_map["price_per_unit"] = col
            elif "total" in lower and "amount" in lower:
                col_map["total_amount"] = col
            elif "date" in lower:
                col_map["date"] = col
            elif "region" in lower or "city" in lower or "location" in lower:
                col_map["region"] = col
        return col_map

    cols = auto_detect_columns(df)
    st.info(f"🧠 Auto-detected columns: {cols}")

    # ✅ Auto Insights
    st.subheader("📈 Auto Insights")

    # Convert Date column to datetime if exists
    if cols["date"]:
        df[cols["date"]] = pd.to_datetime(df[cols["date"]], errors="coerce")

    # 💰 Total Sales by Region (Bar Chart)
    if cols["region"] and cols["total_amount"]:
        region_sales = df.groupby(cols["region"])[cols["total_amount"]].sum().sort_values(ascending=False)
        st.write("🌍 Total Sales by Region")
        st.bar_chart(region_sales)

    # 📉 Most Sales per Region (Line Chart)
    if cols["region"] and cols["total_amount"] and cols["date"]:
        df_line = df.copy()
        df_line["Month"] = df_line[cols["date"]].dt.to_period("M").astype(str)
        line_data = df_line.groupby(["Month", cols["region"]])[cols["total_amount"]].sum().unstack().fillna(0)
        st.write("📉 Monthly Sales per Region (Line Chart)")
        st.line_chart(line_data)

    # 🛒 Top Selling Product Category per Region
    if cols["region"] and cols["product_category"] and cols["total_amount"]:
        st.write("🏆 Top Selling Product Category per Region")
        region_top_products = (
            df.groupby([cols["region"], cols["product_category"]])[cols["total_amount"]]
            .sum()
            .reset_index()
            .sort_values(cols["total_amount"], ascending=False)
        )

        top_products_by_region = region_top_products.groupby(cols["region"]).first().reset_index()
        st.dataframe(top_products_by_region)

    # 🔝 Most Sold Product Category (Overall)
    if cols["product_category"] and cols["quantity"]:
        st.write("🔝 Most Sold Product Category Overall (By Quantity)")
        most_sold = (
            df.groupby(cols["product_category"])[cols["quantity"]]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(most_sold)

    # 📅 Monthly Sales Trend
    if cols["date"] and cols["total_amount"]:
        df_monthly = df.copy()
        df_monthly["Month"] = df_monthly[cols["date"]].dt.to_period("M").astype(str)
        monthly_sales = df_monthly.groupby("Month")[cols["total_amount"]].sum()
        st.write("🗓️ Monthly Sales Trend")
        st.line_chart(monthly_sales)

    # 💰 Total Sales Metric
    if cols["total_amount"]:
        total_sales = df[cols["total_amount"]].sum()
        st.metric("💰 Total Sales", f"{total_sales:,.2f}")

    # 💬 LLM Q&A
    st.subheader("💬 Ask a question about your data")
    user_question = st.text_input("Ask me anything like 'Which region sold the most electronics?'")

    if user_question:
        csv_data = df.head(30).to_csv(index=False)
        prompt = f"""You are a smart data analyst. Here's a sample of the Excel data:\n\n{csv_data}\n\nNow answer this question clearly and briefly:\n\n{user_question}"""

        with st.spinner("Thinking..."):
            response = model.generate(prompt, max_tokens=512)
            st.success("Answer:")
            st.write(response.strip())
