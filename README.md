# ShopSphere Pro – E-Commerce Platform Backend

ShopSphere Pro is a backend application for an e-commerce platform built using **FastAPI, Python, MySQL, SQLAlchemy, and JWT Authentication**.

The system provides APIs for authentication, user management, customer profiles, address management, product categories, brands, products, product variants, and product media management.

## 🚀 Tech Stack

- **Backend:** Python, FastAPI
- **Database:** MySQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT Access & Refresh Tokens
- **Password Hashing:** Argon2
- **Validation:** Pydantic
- **API Documentation:** Swagger UI
- **File Upload:** FastAPI UploadFile

## 📌 Project Modules

### Module 01 – Authentication & Authorization
- Customer registration
- Customer and employee login
- JWT access and refresh tokens
- Token refresh and logout
- Password hashing
- Role-based access control (RBAC)

### Module 02 – User Management
- List and search users
- Filter users by role
- Update user information and roles
- Deactivate user accounts

### Module 03 – Customer Registration
- Customer registration
- Email validation
- Duplicate email prevention
- Email verification token flow

### Module 04 – Customer Profile
- View customer profile
- Update profile information
- Profile change history
- Customer account deactivation

### Module 05 – Address Management
- Create customer addresses
- View saved addresses
- Update addresses
- Delete addresses
- Billing and shipping address types
- Default address management

### Module 06 – Category Management
- Create categories
- View categories
- Update categories
- Delete categories
- Parent and child category support
- Active and inactive status

### Module 07 – Brand Management
- Create and manage brands
- Update brand information
- Activate and deactivate brands
- Retrieve products by brand

### Module 08 – Product Management
- Create and manage products
- Unique product SKU
- Category and brand association
- Product search
- Filter products by category, brand, and price

### Module 09 – Product Variants
- Create product variants
- Manage size and color variations
- Unique variant SKU
- Variant-specific price
- Stock quantity management

### Module 10 – Product Images & Documents
- Upload product images and PDF documents
- Associate media with products and variants
- Retrieve uploaded media
- Delete media files
- File type and size validation

## 👥 Supported User Roles

- Super Admin
- Admin
- Product Manager
- Inventory Manager
- Order Manager
- Support Agent
- Customer
- Delivery Manager
- Finance Manager

## 📁 Project Structure

```text
ShopSphere_Pro/
│
├── app/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── dependencies.py
│   │
│   ├── db/
│   │   ├── database.py
│   │   ├── init_db.py
│   │   └── create_admin.py
│   │
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   ├── utils/
│   ├── middleware/
│   │
│   └── main.py
│
├── uploads/
│   └── products/
│
├── tests/
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## ⚙️ Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/kathirvelp39/ShopSphere-Pro.git
cd ShopSphere-Pro
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate virtual environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root using `.env.example` as a reference.

Configure the following values:

```env
PROJECT_NAME=ShopSphere Pro

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=shopsphere_pro

SECRET_KEY=your_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

UPLOAD_DIR=uploads/products
MAX_UPLOAD_SIZE=5242880
```

**Important:** Never commit your actual `.env` file or database credentials to GitHub.

### 6. Create database tables

Make sure MySQL is running and the `shopsphere_pro` database exists.

```bash
python -m app.db.init_db
```

### 7. Create Super Admin account

```bash
python -m app.db.create_admin
```

### 8. Start the FastAPI server

```bash
uvicorn app.main:app --reload
```

## 📖 API Documentation

After starting the application, access the Swagger documentation:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **Health Check:** http://127.0.0.1:8000/health

API base path:

```text
/api/v1
```

## 🔐 Security Features

- JWT-based authentication
- Access and refresh token sessions
- Token revocation
- Argon2 password hashing
- Role-based authorization
- Protected management endpoints
- File upload validation
- Environment-based configuration

## 🗄️ Database

The application uses MySQL with SQLAlchemy ORM for database operations.

Database tables are created through the project's database initialization script.

## 🧪 Testing

API endpoints can be tested using:

- Swagger UI
- Postman

## 👨‍💻 Developer

**Kathirvel P.**

Python Backend Developer

GitHub: https://github.com/kathirvelp39

## 📌 Project Status

**Day 01 – Modules 1 to 10**

Core backend setup, database integration, authentication, user management, customer management, address management, and product catalog APIs have been implemented.

API testing and further improvements are ongoing.

---

**ShopSphere Pro – E-Commerce Platform Backend**
