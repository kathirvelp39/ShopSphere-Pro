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


# ShopSphere Pro – Day 02
## Advanced E-Commerce Backend Modules (11–20)

Day 02 focuses on advanced e-commerce functionalities, including product attributes, pricing, inventory, warehouses, shopping carts, wishlists, and coupons.

The backend is developed using **FastAPI, Python, SQLAlchemy, Pydantic, and MySQL**.

---

## Module 11 – Product Attribute Management

### Purpose
Product attributes help customers understand the specifications and characteristics of a product.

### What it does
- Creates product attributes such as Size, Color, Material, and Weight.
- Assigns attribute values to individual products.
- Retrieves product-specific attributes.
- Removes attributes from products.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/attributes` | Create a product attribute |
| GET | `/api/v1/attributes` | Retrieve attributes |
| POST | `/api/v1/products/{product_id}/attributes` | Assign attributes to a product |
| GET | `/api/v1/products/{product_id}/attributes` | Get product attributes |
| DELETE | `/api/v1/products/{product_id}/attributes/{attribute_id}` | Remove a product attribute |

### Working Explanation
The system stores attribute definitions separately and connects their values to products. This allows different products to have different specifications without creating separate database columns for every possible attribute.

---

## Module 12 – Product Pricing Management

### Purpose
Manages product prices and maintains a history of price changes.

### What it does
- Maintains base product prices.
- Supports sale price updates.
- Tracks previous and updated prices.
- Provides product price history.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| PATCH | `/api/v1/products/{product_id}/price` | Update product price |
| GET | `/api/v1/products/{product_id}/price-history` | Retrieve price history |

### Working Explanation
Whenever a product price is updated, the system can maintain a record of the previous and new prices. This helps administrators track pricing changes over time.

---

## Module 13 – Inventory Management

### Purpose
Tracks product stock quantities and inventory movements.

### What it does
- Creates inventory records.
- Tracks available and reserved stock.
- Adjusts stock quantities.
- Records inventory movements.
- Retrieves inventory movement history.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/inventory` | Create inventory |
| GET | `/api/v1/inventory` | Retrieve inventory |
| POST | `/api/v1/inventory/{inventory_id}/adjust` | Adjust stock quantity |
| GET | `/api/v1/inventory/{inventory_id}/movements` | View stock movement history |

### Working Explanation
Inventory management helps the business monitor product stock levels. Stock adjustments and movement records provide a history of inventory changes.

---

## Module 14 – Warehouse Management

### Purpose
Manages warehouse information and warehouse-related inventory.

### What it does
- Creates warehouse records.
- Retrieves warehouse information.
- Activates or deactivates warehouses.
- Displays inventory stored in a particular warehouse.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/warehouses` | Create a warehouse |
| GET | `/api/v1/warehouses` | Retrieve warehouses |
| PATCH | `/api/v1/warehouses/{warehouse_id}/status` | Update warehouse status |
| GET | `/api/v1/warehouses/{warehouse_id}/inventory` | View warehouse inventory |

### Working Explanation
The system organizes inventory based on warehouse locations. This helps administrators understand where products are stored and manage warehouse availability.

---

## Module 15 – Inventory Transfer Management

### Purpose
Transfers stock between warehouses.

### What it does
- Creates inventory transfer requests.
- Dispatches stock from a source warehouse.
- Receives stock at a destination warehouse.
- Retrieves transfer details.
- Tracks the transfer process.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/inventory-transfers` | Create an inventory transfer |
| POST | `/api/v1/inventory-transfers/{transfer_id}/dispatch` | Dispatch inventory |
| POST | `/api/v1/inventory-transfers/{transfer_id}/receive` | Receive inventory |
| GET | `/api/v1/inventory-transfers/{transfer_id}` | Retrieve transfer details |

### Working Explanation
Inventory transfers help move products between warehouses. The transfer process separates dispatch and receiving operations so that stock movement can be tracked.

---

## Module 16 – Low-Stock Management

### Purpose
Identifies products that have reached or fallen below their configured stock threshold.

### What it does
- Configures low-stock thresholds.
- Updates inventory alert thresholds.
- Retrieves products with low stock.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| PATCH | `/api/v1/inventory/{inventory_id}/low-stock-threshold` | Update low-stock threshold |
| GET | `/api/v1/inventory/low-stock` | Retrieve low-stock inventory |

### Working Explanation
Each inventory record can have a minimum stock threshold. The low-stock endpoint helps administrators identify inventory that may need replenishment.

---

## Module 17 – Shopping Cart Management

### Purpose
Allows customers to manage products they intend to purchase.

### What it does
- Creates or retrieves a shopping cart.
- Adds products to the cart.
- Retrieves cart items.
- Updates item quantities.
- Removes individual cart items.
- Clears the shopping cart.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/cart` | Create or access cart |
| GET | `/api/v1/cart` | Retrieve cart |
| DELETE | `/api/v1/cart` | Clear cart |
| POST | `/api/v1/cart/items` | Add an item |
| PATCH | `/api/v1/cart/items/{item_id}` | Update cart item |
| DELETE | `/api/v1/cart/items/{item_id}` | Remove cart item |

### Working Explanation
The shopping cart stores products selected by a customer before checkout. Customers can add products, change quantities, and remove unwanted items.

---

## Module 18 – Cart Price Calculation

### Purpose
Calculates the price summary of the products in a shopping cart.

### What it does
- Calculates the cart subtotal.
- Provides a price summary.
- Helps customers review the cart value before checkout.

### API Endpoint

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/cart/price-summary` | Calculate cart price summary |

### Working Explanation
The price summary provides a consolidated view of the cart value based on its items. It helps customers understand the amount associated with their selected products before proceeding.

---

## Module 19 – Wishlist Management

### Purpose
Allows customers to save products they may want to purchase later.

### What it does
- Adds products to a wishlist.
- Retrieves wishlist products.
- Removes products from a wishlist.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/wishlist/{product_id}` | Add product to wishlist |
| GET | `/api/v1/wishlist` | Retrieve wishlist |
| DELETE | `/api/v1/wishlist/{product_id}` | Remove product from wishlist |

### Working Explanation
A wishlist stores products separately from the shopping cart. Customers can save interesting products without immediately adding them to their cart.

---

## Module 20 – Coupon Management

### Purpose
Manages discount coupons and validates coupon codes.

### What it does
- Creates discount coupons.
- Retrieves available coupons.
- Activates or deactivates coupons.
- Validates coupon codes.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/coupons` | Create a coupon |
| GET | `/api/v1/coupons` | Retrieve coupons |
| PATCH | `/api/v1/coupons/{coupon_id}/status` | Update coupon status |
| POST | `/api/v1/coupons/validate` | Validate a coupon code |

### Working Explanation
Coupon management allows administrators to maintain discount codes. Customers can submit a coupon code for validation before using it during a purchase.

---

## Day 02 – Technical Implementation

The Day 02 modules extend the existing ShopSphere Pro backend with:

- SQLAlchemy database models.
- Pydantic request and response schemas.
- FastAPI API routers.
- MySQL database integration.
- Inventory and product-related data management.
- API documentation through Swagger UI.
- Authentication and authorization integration.

## Database Tables

The Day 02 implementation includes tables for:

- Product Attributes and Attribute Values
- Product Price History
- Inventory and Inventory Movements
- Warehouses
- Stock Transfers and Transfer Items
- Shopping Carts and Cart Items
- Wishlists and Wishlist Items
- Coupons

## API Documentation

Start the FastAPI application:

```bash
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Project Progress

| Development Day | Modules | Description |
|---|---|---|
| Day 01 | 1–10 | Authentication, Users, Categories, Brands, Products and Variants |
| Day 02 | 11–20 | Attributes, Pricing, Inventory, Warehouses, Cart, Wishlist and Coupons |

**Project:** ShopSphere Pro  
**Development:** Backend Only  
**Framework:** FastAPI  
**Database:** MySQL  
**ORM:** SQLAlchemy  
**Validation:** Pydantic  
**API Testing:** Swagger UI / Postman