# Sales_Management_System


The Sales Management System is a role-based web application developed using Python, Streamlit, PostgreSQL, and Plotly to streamline sales operations and payment tracking. The system enables organizations to manage branch-wise sales data, monitor customer payments, and analyze business performance through interactive dashboards.

The application supports two user roles: Super Admin and Admin. Super Admins can access and manage data across all branches, while Admins are restricted to viewing and managing records related to their assigned branch. This role-based access control ensures secure and organized data management.

The system is built on a normalized PostgreSQL database consisting of four core tables: branches, users, customer_sales, and payment_splits. Foreign key relationships maintain data integrity, while a PostgreSQL trigger automatically updates the received amount whenever a payment is recorded, eliminating manual calculations and ensuring accurate pending balance tracking.

Key features of the system include sales entry management, payment tracking, branch-wise performance monitoring, user authentication, role-based authorization, automated database operations, and interactive data visualization. The dashboard provides business insights through dynamic charts, KPI metrics, and filters that help users analyze sales trends and payment status effectively.

This project demonstrates practical implementation of database design, SQL triggers, backend integration, data visualization, and web application development using modern Python technologies. It serves as a complete business intelligence solution for managing sales and payment operations efficiently.

## Technologies Used

* Python
* Streamlit
* PostgreSQL
* pgAdmin
* SQLAlchemy
* psycopg2
* Plotly
* Pandas

## Key Features

* Role-Based Authentication (Super Admin / Admin)
* Branch-Level Access Control
* Customer Sales Management
* Payment Tracking System
* Automated Trigger-Based Updates
* Interactive Dashboard and KPIs
* Dynamic Filters and Visualizations
* PostgreSQL Relational Database
* Secure Data Management
* Business Performance Monitoring
