import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
import plotly.express as px
import time

# ── DB CONNECTION ──
def get_conn():
    return psycopg2.connect(
        host="localhost",
        dbname="sales_management_system",
        user="postgres",
        password="Shivani1234",
        port=5432
    )

def run_query(sql, params=None):
    conn = get_conn()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or ())
    data = cur.fetchall()
    conn.close()
    return pd.DataFrame(data)

# ── LOGIN FUNCTION ──
def login(username, password):
    df = run_query(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    return df.iloc[0] if not df.empty else None

# ── SESSION ──
if "user" not in st.session_state:
    st.session_state.user = None


# LOGIN PAGE

if st.session_state.user is None:
    st.title("🔐 Login Page")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login(username, password)
        if user is not None:
            st.session_state.user = user
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")
# ── MAIN APP ──
else:
    user = st.session_state.user
    role = user["role"]
    branch_id = user["branch_id"]

    st.sidebar.write(f"👤 {user['username']}")
    st.sidebar.write(f"Role: {role}")

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    # ____NAVIGATION____
    page = st.sidebar.selectbox(
        "📌 Navigation",["Dashboard", "Add Sales", "Add Payment", "SQL Queries"]
    )  

    if page == "Dashboard":
        st.title("📊 Sales Dashboard")
        
        # ─────────────────────────────
        # LOAD DATA
        # ─────────────────────────────
        df = run_query("""
        SELECT cs.sale_id, cs.date, cs.branch_id,
               b.branch_name,
               cs.name, cs.mobile_number, cs.product_name,
               cs.gross_sales, cs.received_amount,
               cs.pending_amount, cs.status
        FROM customer_sales cs
        JOIN branches b ON cs.branch_id = b.branch_id
        """)

        # ─────────────────────────────
        # ROLE FILTER
        # ─────────────────────────────
        if role == "Admin":
            df = df[df["branch_id"] == branch_id]

        # ─────────────────────────────
        # FILTERS
        # ─────────────────────────────
        col1, col2, col3 = st.columns(3)

        with col1:
            if role == "Admin":
                branch_filter = df["branch_name"].iloc[0]
                st.selectbox("Branch", [branch_filter], disabled=True)
            else:
                branch_filter = st.selectbox(
                    "Branch",
                    ["All"] + list(df["branch_name"].unique())
                )

        with col2:
            product_filter = st.selectbox(
                "Product",
                ["All"] + list(df["product_name"].unique())
            )

        with col3:
            status_filter = st.selectbox(
                "Status",["All"] + list(df["status"].unique())
            )       

        # APPLY FILTERS
        if role != "Admin" and branch_filter != "All":
            df = df[df["branch_name"] == branch_filter]

        if product_filter != "All":
            df = df[df["product_name"] == product_filter]

        if status_filter != "All":
            df = df[df["status"] == status_filter]
        
        # ─────────────────────────────
        # DATE FILTER
        # ─────────────────────────────
        # Convert date column
        df["date"] = pd.to_datetime(df["date"])
        # Get min & max date
        min_date = df["date"].min().date()
        max_date = df["date"].max().date()
        
        # Initialize session state only once
        if "start_date" not in st.session_state:
            st.session_state.start_date = min_date
        if "end_date" not in st.session_state:
            st.session_state.end_date = max_date


        # UI (same row)
        d1, d2, d3 = st.columns([3, 3, 1])
        with d1:
            start_date = st.date_input(
                "Start Date",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key='start_date'
            )
        with d2:
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key='end_date'
            )
        with d3:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄Reset Dates"):
                # DELETE KEY
                del st.session_state['start_date']
                del st.session_state['end_date']
                st.rerun()
                
        # Apply filter
        df = df[
            (df["date"] >= pd.to_datetime(start_date)) &
            (df["date"] <= pd.to_datetime(end_date))
        ]

        # ─────────────────────────────
        # SAFE CHECK
        # ─────────────────────────────
        if df.empty:
            st.warning("No data available for selected filters")
            st.stop()

        # ─────────────────────────────
        # RANGE SLIDER
        # ─────────────────────────────
        min_val = int(df["gross_sales"].min())
        max_val = int(df["gross_sales"].max())

        if min_val == max_val:
            max_val += 1

        gross_range = st.slider(
            "Gross Sales Range ₹",
            min_val,
            max_val,
            (min_val, max_val)
        )

        df = df[
            (df["gross_sales"] >= gross_range[0]) &
            (df["gross_sales"] <= gross_range[1])
        ]

        # ─────────────────────────────
        # KPI
        # ─────────────────────────────
        kpi1, kpi2, kpi3 = st.columns(3)

        kpi1.metric("Total Sales", f"₹{df['gross_sales'].sum():,.0f}")
        kpi2.metric("Received", f"₹{df['received_amount'].sum():,.0f}")
        kpi3.metric("Pending", f"₹{df['pending_amount'].sum():,.0f}")

        st.markdown("---")
        # TABLE
        st.markdown("### 📋 Sales Data")
        st.dataframe(df,  width="stretch")

        # CHARTS
        c1, c2 = st.columns(2)

        with c1:
            fig1 = px.pie(
                df,
                names="status",
                values="gross_sales",
                hole=0.5,
                title="Sales Status Distribution"
            )
            st.plotly_chart(fig1,  width="stretch")

        with c2:
            df_bar = df.groupby("product_name")["gross_sales"].sum().reset_index()

            fig2 = px.bar(
                df_bar,
                x="product_name",
                y="gross_sales",
                title="Product-wise Sales"
            )
            st.plotly_chart(fig2,  width="stretch")

    # ─────────────────────────────
    # ADD SALES SECTION
    # ─────────────────────────────
    elif page == "Add Sales":
        st.title("➕ Add Sales")
        # BRANCH LOGIC
        if role == "Super Admin":
            # Fetch all branches
            branch_df = run_query("SELECT branch_id, branch_name FROM branches")

            branch_dict = dict(zip(branch_df["branch_name"], branch_df["branch_id"]))

            selected_branch = st.selectbox(
                "Select Branch",
                list(branch_dict.keys())
            )

            branch_id = branch_dict[selected_branch]
        else:
            # Admin - fixed branch
            branch_id = user["branch_id"]

            # show branch name (optional UI)
            branch_name = run_query(
                "SELECT branch_name FROM branches WHERE branch_id=%s",
                (int(branch_id),)
            )

            if not branch_name.empty:
                st.text_input(
                    "Branch",
                    value=branch_name["branch_name"].iloc[0],
                    disabled=True
                )
        # FORM
        with st.form("sales_form",clear_on_submit=True):
                name = st.text_input("Customer Name")
                mobile_number = st.text_input("Mobile Number")
                product_name = st.text_input("Product Name")
                gross_sales = st.number_input("Gross Sales ₹", min_value=0)
                date = st.date_input("Date")

                submit = st.form_submit_button("Add Sale")

                if submit:
                    if not name:
                        st.error("Name required")
                    elif len(mobile_number) != 10:
                        st.error("Enter valid mobile number")
                    elif branch_id is None:
                        st.error("Branch not selected")
                    elif gross_sales <= 0:
                        st.error("Enter valid gross sales amount")
                    else:
                        check = run_query(
                            "SELECT name FROM customer_sales WHERE mobile_number=%s",
                            (str(mobile_number),)
                        )
                        if not check.empty:
                            exiting_name = check["name"].iloc[0]
                            st.warning(f"Data already exists for {exiting_name}. Please verify.")
                        else:
                            conn = get_conn()
                            cur = conn.cursor()
                            

                            cur.execute("""
                            SELECT setval(
                                'customer_sales_sale_id_seq',
                                COALESCE((SELECT MAX(sale_id) FROM customer_sales), 0)
                                )
                                """)
                            cur.execute("""
                            INSERT INTO customer_sales
                                (date, branch_id, name, mobile_number,
                                product_name, gross_sales,
                                received_amount, status)
                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                            """, (
                                date, int(branch_id), str(name), str(mobile_number),
                                str(product_name), int(gross_sales), 0, "Open"
                            ))

                            conn.commit()
                            cur.close()
                            conn.close()
                            st.success("Sale added successfully!")
                            time.sleep(1)
                            st.rerun()

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ADD PAYMENT SECTION
    elif page == "Add Payment":
        st.title("💰 Add Payment")
        # ROLE BASE ACCESS
        if role not in ["Admin", "Super Admin"]:
            st.warning("You don't have access to this page")
            st.stop()
            # SEARCH MACHANISHM
        search = st.text_input("🔍 Search by Name / Mobile (Optional)")
        query = """
            SELECT sale_id, name, mobile_number,
            product_name, gross_sales,
            received_amount, pending_amount,
            branch_id
            FROM customer_sales
            WHERE pending_amount > 0
    """  
        sales_df = run_query(query)
        # ROLE FILTER
        if role == "Admin":
            sales_df = sales_df[sales_df["branch_id"] == branch_id]
        # SEARCH FILTER
        if search:
            search = search.strip()
            sales_df = sales_df[
                sales_df["name"].str.contains(search, case=False, na=False)
                | sales_df["mobile_number"].astype(str).str.contains(search)
            ]
        if sales_df.empty:
            st.warning("No pending sales found")
            st.stop()
        # SELECT SALE
        sales_df["label"] = (
            sales_df["sale_id"].astype(str)
            + " | "
            + sales_df["name"].astype(str)
            + " | Pending ₹"
            + sales_df["pending_amount"].astype(str)
        )
        selected_label = st.selectbox(
            "Select Sale",
            sales_df["label"]
        )
        selected_sale_id = int(selected_label.split("|")[0])
        selected_row = sales_df[sales_df["sale_id"] == selected_sale_id].iloc[0]
        # PAYMENT FORM
        with st.form("payment_form"):
            st.write(f"👤 Customer: {selected_row['name']}")
            st.write(f"📱 Mobile: {selected_row['mobile_number']}")
            st.write(f"⏳ Pending: ₹{selected_row['pending_amount']}")
            payment_method = st.selectbox(
                "Payment Method",
                ["Cash", "Card", "UPI"]
            )
            pending_amt = float(selected_row["pending_amount"])
            amount_paid = st.number_input(
                "Amount Paid ₹",
                min_value=0.0,
                max_value=pending_amt,
                value=0.0,
                placeholder='Enter amount',
                step=0.01)
            
            submit_payment = st.form_submit_button("Submit Payment")
            if submit_payment:
                if amount_paid is None or amount_paid <= 0:
                    st.error("Enter valid amount")

                else:
                    conn = get_conn()
                    cur = conn.cursor()

                    cur.execute("""
                        INSERT INTO payment_splits
                        (sale_id, amount_paid, payment_method, payment_date)
                        VALUES (%s,%s,%s,%s)
                    """, (
                        selected_sale_id,
                        int(amount_paid),
                        payment_method,
                        pd.to_datetime("today").date()
                    ))

                    conn.commit()
                    cur.close()
                    conn.close()

                    st.success("✅ Payment added successfully!")
                    time.sleep(1)
                    st.rerun()
# SQL QUERIES PAGE CODE
    elif page == "SQL Queries":

        st.title("💻 SQL Queries")

        query_options = [
            "1. All customer sales",
            "2. All branches",
            "3. All payment splits",
            "4. Sales with status Open",
            "5. Sales from Chennai branch",
            "6. Total gross sales",
            "7. Total received amount",
            "8. Total pending amount",
            "9. Sales count per branch",
            "10. Average gross sales",
            "11. Sales data",
            "12. Sales with total payment",
            "13. Branch-wise gross sales",
            "14. Sales with payment method",
            "15. Sales with branch admin",
            "16. Pending amount > 5000",
            "17. Top 3 highest gross sales",
            "18. Branch with highest sales",
            "19. Monthly sales summary",
            "20. Payment method-wise collection"
        ]

        query_option = st.selectbox("Select Query", query_options)

        if st.button("Run Query"):

            query = None
            params = None

            # 1 — ALL SALES
            if query_option == "1. All customer sales":

                query = "SELECT * FROM customer_sales"

                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)

            # 2 — BRANCHES
            elif query_option == "2. All branches":
                query = "SELECT * FROM branches"

            # 3 — PAYMENT SPLITS
            elif query_option == "3. All payment splits":

                query = """
                    SELECT ps.*
                    FROM payment_splits ps
                    JOIN customer_sales cs
                    ON ps.sale_id = cs.sale_id
                """

                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"
                    params = (int(branch_id),)

            # 4 — OPEN SALES
            elif query_option == "4. Sales with status Open":

                query = """
                    SELECT *
                    FROM customer_sales
                    WHERE status = 'Open'
                """

                if role == "Admin":
                    query += " AND branch_id = %s"
                    params = (int(branch_id),)

            # 5 — CHENNAI
            elif query_option == "5. Sales from Chennai branch":

                query = """
                    SELECT cs.*
                    FROM customer_sales cs
                    JOIN branches b
                    ON cs.branch_id = b.branch_id
                    WHERE b.branch_name = 'Chennai'
                """

                if role == "Admin":
                    query += " AND cs.branch_id = %s"
                    params = (int(branch_id),)

            # 6 — TOTAL GROSS
            elif query_option == "6. Total gross sales":

                query = "SELECT SUM(gross_sales) AS total_gross_sales FROM customer_sales"

                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)

            # 7 — TOTAL RECEIVED
            elif query_option == "7. Total received amount":

                query = "SELECT SUM(received_amount) AS total_received FROM customer_sales"

                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)

            # 8 — TOTAL PENDING
            elif query_option == "8. Total pending amount":

                query = "SELECT SUM(pending_amount) AS total_pending FROM customer_sales"

                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)
            # 9 — SALES COUNT PER BRANCH
            elif query_option == "9. Sales count per branch":

                query = """
                    SELECT 
                        b.branch_name,
                        COUNT(cs.sale_id) AS total_sales
                    FROM customer_sales cs
                    JOIN branches b
                    ON cs.branch_id = b.branch_id
                """

                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"

                    if role == "Admin":
                        params = (int(branch_id),)
                query += " GROUP BY b.branch_name ORDER BY total_sales DESC"
            # 10 — AVERAGE GROSS SALES
            elif query_option == "10. Average gross sales":
                query = "SELECT AVG(gross_sales) AS avg_gross_sales FROM customer_sales"
                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)
            # 11 — SALES DATA
            elif query_option == "11. Sales data":

                    query = """
                        SELECT 
                            cs.sale_id,
                            b.branch_name,
                            cs.name,
                            cs.mobile_number,
                            cs.product_name,
                            cs.gross_sales,
                            cs.received_amount,
                            cs.pending_amount
                        FROM customer_sales cs
                        JOIN branches b
                        ON cs.branch_id = b.branch_id
                    """

                    if role == "Admin":
                        query += " WHERE cs.branch_id = %s"
                        params = (int(branch_id),)
            # 12. Sales with total payment
            elif query_option == "12. Sales with total payment":

                query = """
                    SELECT 
                        cs.sale_id,
                        cs.name,
                        cs.product_name,
                        cs.gross_sales,
                        COALESCE(SUM(ps.amount_paid),0) AS total_paid
                    FROM customer_sales cs
                    LEFT JOIN payment_splits ps
                    ON cs.sale_id = ps.sale_id
                """

                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"

                query += " GROUP BY cs.sale_id, cs.name, cs.product_name, cs.gross_sales"

                if role == "Admin":
                    params = (int(branch_id),)
            # 13. Branch-wise gross sales
            elif query_option == "13. Branch-wise gross sales":
                query = """
                        SELECT 
                            b.branch_name,
                            SUM(cs.gross_sales) AS total_sales
                        FROM customer_sales cs
                        JOIN branches b
                        ON cs.branch_id = b.branch_id
                    """
                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"
                    params = (int(branch_id),)
                query += " GROUP BY b.branch_name ORDER BY total_sales DESC"
            # 14. Sales with Payment Method
            elif query_option == "14. Sales with payment method":

                query = """
                    SELECT 
                        cs.sale_id,
                        cs.name,
                        cs.product_name,
                        ps.payment_method,
                        ps.amount_paid
                    FROM customer_sales cs
                    JOIN payment_splits ps
                    ON cs.sale_id = ps.sale_id
                """
                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"
                    params = (int(branch_id),)
            # 15. Sales with Branch Admin
            elif query_option == "15. Sales with branch admin":

                query = """
                    SELECT 
                        cs.sale_id,
                        cs.name,
                        cs.product_name,
                        cs.gross_sales,
                        cs.received_amount,
                        cs.pending_amount,
                        b.branch_name,
                        b.branch_admin_name
                    FROM customer_sales cs
                    JOIN branches b
                    ON cs.branch_id = b.branch_id
                """

                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"
                    params = (int(branch_id),)
            # 16 — PENDING > 5000
            elif query_option == "16. Pending amount > 5000":

                query = "SELECT * FROM customer_sales WHERE pending_amount > 5000"

                if role == "Admin":
                    query += " AND branch_id = %s"
                    params = (int(branch_id),)

            # 17 — TOP 3
            elif query_option == "17. Top 3 highest gross sales":

                query = "SELECT * FROM customer_sales"

                if role == "Admin":
                    query += " WHERE branch_id = %s"

                query += " ORDER BY gross_sales DESC LIMIT 3"

                if role == "Admin":
                    params = (int(branch_id),)
            # 18. Branch with Highest Sales
            elif query_option == "18. Branch with highest sales":

                query = """
                    SELECT 
                        b.branch_name,
                        SUM(cs.gross_sales) AS total_sales
                    FROM customer_sales cs
                    JOIN branches b
                    ON cs.branch_id = b.branch_id
                """

                if role == "Admin":
                    query += " WHERE cs.branch_id = %s"

                query += " GROUP BY b.branch_name ORDER BY total_sales DESC LIMIT 1"

                if role == "Admin":
                    params = (int(branch_id),)
            # 19. Monthly Sales Summary
            elif query_option == "19. Monthly sales summary":

                query = """
                    SELECT 
                        TO_CHAR(DATE_TRUNC('month', date), 'Mon YYYY') AS month,
                        COUNT(*) AS sale_count,
                        SUM(gross_sales) AS total_sales
                    FROM customer_sales
                """

                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)

                query += "GROUP BY month ORDER BY month"
            # 20 — PAYMENT METHOD
            elif query_option == "20. Payment method-wise collection":

                query = """
                    SELECT payment_method,
                        SUM(amount_paid) AS total_collection
                    FROM payment_splits
                    GROUP BY payment_method
                """
                if role == "Admin":
                    query += " WHERE branch_id = %s"
                    params = (int(branch_id),)

            #  SAFETY CHECK
            if query is None:
                st.error("Query not defined properly")
                st.stop()

            #  RUN QUERY
            if params:
                df = run_query(query, params)
            else:
                df = run_query(query)
            if df.empty and query_option == "5. Sales from Chennai branch" and role == "Admin":
                st.error("❌ You don't have access to view data")
                st.stop()


            st.dataframe(df, use_container_width=True)