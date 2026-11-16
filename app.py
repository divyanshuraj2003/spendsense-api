import streamlit as st
import pandas as pd
from database import engine, Base, SessionLocal
from models import User, Transaction
from auth import hash_pwd, check_pwd

# Initialize database tables
Base.metadata.create_all(bind=engine)

st.set_page_config(page_title="SpendSense - Expense Tracker", layout="wide")

# Hide Streamlit developer toolbar & footer for a clean hosted look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

db = SessionLocal()

# --- LOGIN / REGISTER SCREEN ---
if st.session_state.user_id is None:
    st.title("SpendSense — Personal Expense & Analytics")
    st.caption("Track expenses, import CSV statements, and detect spending anomalies.")

    tab1, tab2 = st.tabs(["Login", "Create Account"])

    with tab1:
        with st.form("login_form"):
            uname = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = db.query(User).filter(User.username == uname.strip()).first()
                if user and check_pwd(pwd, user.hashed_password):
                    st.session_state.user_id = user.id
                    st.session_state.username = user.username
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    with tab2:
        with st.form("register_form"):
            new_uname = st.text_input("Choose Username")
            new_pwd = st.text_input("Choose Password", type="password")
            reg_btn = st.form_submit_button("Sign Up")
            if reg_btn:
                if not new_uname.strip() or not new_pwd:
                    st.warning("Both fields are required")
                elif db.query(User).filter(User.username == new_uname.strip()).first():
                    st.error("Username already taken")
                else:
                    u = User(username=new_uname.strip(), hashed_password=hash_pwd(new_pwd))
                    db.add(u)
                    db.commit()
                    st.success("Account created! Switch to the Login tab.")

# --- MAIN DASHBOARD ---
else:
    col_head, col_logout = st.columns([6, 1])
    with col_head:
        st.title(f"SpendSense Dashboard — {st.session_state.username}")
    with col_logout:
        if st.button("Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    st.divider()

    # Left sidebar for adding transactions or uploading CSV
    with st.sidebar:
        st.header("Add Transaction")
        with st.form("add_tx_form", clear_on_submit=True):
            title = st.text_input("Title (e.g., Swiggy, Rent)")
            amount = st.number_input("Amount", min_value=1.0, step=10.0)
            category = st.selectbox("Category", ["Food", "Rent", "Travel", "Utilities", "Electronics", "Income", "Misc"])
            tx_type = st.radio("Type", ["EXPENSE", "INCOME"], horizontal=True)
            if st.form_submit_button("Save Entry"):
                if title.strip():
                    db.add(Transaction(
                        title=title.strip(),
                        amount=float(amount),
                        category=category,
                        tx_type=tx_type,
                        user_id=st.session_state.user_id
                    ))
                    db.commit()
                    st.success("Saved!")
                    st.rerun()

        st.divider()
        st.header("Bulk Import CSV")
        st.caption("Columns required: title, amount, category")
        uploaded = st.file_uploader("Upload bank/UPI CSV", type=["csv"])
        if uploaded and st.button("Import Rows"):
            df_csv = pd.read_csv(uploaded)
            df_csv.columns = [c.strip().lower() for c in df_csv.columns]
            if {"title", "amount", "category"}.issubset(set(df_csv.columns)):
                df_csv = df_csv.dropna(subset=["title", "amount"])
                df_csv["category"] = df_csv["category"].fillna("Misc").astype(str).str.title()
                df_csv["tx_type"] = df_csv.get("tx_type", "EXPENSE").fillna("EXPENSE").astype(str).str.upper()

                for _, row in df_csv.iterrows():
                    db.add(Transaction(
                        title=str(row["title"]).strip(),
                        amount=float(row["amount"]),
                        category=row["category"],
                        tx_type=row["tx_type"],
                        user_id=st.session_state.user_id
                    ))
                db.commit()
                st.success(f"Imported {len(df_csv)} rows!")
                st.rerun()
            else:
                st.error("CSV missing required columns: title, amount, category")

    # Fetch user transactions
    rows = db.query(Transaction).filter(
        Transaction.user_id == st.session_state.user_id
    ).order_by(Transaction.created_at.desc()).all()

    if not rows:
        st.info("No transactions yet. Use the left sidebar to add an entry or upload sample_statement.csv.")
    else:
        df = pd.DataFrame([{
            "ID": r.id,
            "Title": r.title,
            "Amount": r.amount,
            "Category": r.category,
            "Type": r.tx_type,
            "Date": r.created_at.strftime("%Y-%m-%d %H:%M")
        } for r in rows])

        exp_df = df[df["Type"] == "EXPENSE"]
        inc_df = df[df["Type"] == "INCOME"]

        total_spent = float(exp_df["Amount"].sum()) if not exp_df.empty else 0.0
        total_earned = float(inc_df["Amount"].sum()) if not inc_df.empty else 0.0
        net_balance = total_earned - total_spent

        # Top KPI Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Income", f"₹{total_earned:,.2f}")
        m2.metric("Total Expenses", f"₹{total_spent:,.2f}")
        m3.metric("Net Balance", f"₹{net_balance:,.2f}")

        st.divider()

        # Chart + Anomaly Alerts
        c1, c2 = st.columns([3, 2])
        with c1:
            st.subheader("Spending by Category")
            if not exp_df.empty:
                cat_summary = exp_df.groupby("Category")["Amount"].sum()
                st.bar_chart(cat_summary)
            else:
                st.write("No expense data to chart.")

        with c2:
            st.subheader("Anomaly Alerts (>2x Avg Spend)")
            if len(exp_df) >= 3:
                avg_spend = exp_df["Amount"].mean()
                anomalies = exp_df[exp_df["Amount"] > (avg_spend * 2)]
                if not anomalies.empty:
                    for _, a in anomalies.iterrows():
                        st.warning(f"**{a['Title']}** ({a['Category']}): ₹{a['Amount']:,.2f}")
                else:
                    st.success("No unusual spending spikes detected.")
            else:
                st.caption("Add at least 3 expenses to activate anomaly detection.")

        st.divider()
        st.subheader("Recent Transactions")
        st.dataframe(df.drop(columns=["ID"]), use_container_width=True, hide_index=True)

db.close()
