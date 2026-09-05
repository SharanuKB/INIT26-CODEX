# INIT26-CODEX
# CapitalGuard – Frontend

## 📌 Overview

This folder contains the frontend of **CapitalGuard**, an automated FinTech platform for asset allocation, risk monitoring, market-shock simulation, and portfolio rebalancing.

The frontend provides an interactive dashboard through which users can view portfolio information and interact with the optimization, risk, simulation, and rebalancing features.

---

## 🎯 Frontend Responsibilities

The frontend is responsible for:

* User login interface
* Portfolio dashboard
* Asset allocation visualization
* Risk monitoring
* Portfolio optimization interface
* Market shock simulation
* Rebalancing recommendations
* Responsive UI for desktop and mobile
* Connecting with backend APIs

---

## 🛠️ Technologies Used

* HTML5
* CSS3
* JavaScript
* Chart.js
* Live Server

---

## 📁 Folder Structure

```text
frontend/
│
├── README.md
│
├── index.html
├── dashboard.html
├── optimization.html
├── risk.html
├── simulation.html
├── rebalance.html
│
├── css/
│   └── style.css
│
└── js/
    ├── app.js
    ├── dashboard.js
    ├── optimization.js
    ├── risk.js
    ├── simulation.js
    └── rebalance.js
```

---

## 📄 Pages

### 1. Login – `index.html`

Provides the login interface for accessing the CapitalGuard dashboard.

### 2. Dashboard – `dashboard.html`

Displays:

* Total portfolio value
* Risk score
* Liquidity
* Expected return
* Asset allocation
* Risk alerts
* Recent decisions

### 3. Optimization – `optimization.html`

Allows the user to enter portfolio parameters and view optimized asset allocation.

### 4. Risk Monitor – `risk.html`

Displays portfolio risk indicators and threshold controls.

### 5. Simulation – `simulation.html`

Allows users to simulate financial scenarios such as:

* Market Crash
* Interest Rate Increase
* Liquidity Crisis
* Equity Crash

### 6. Rebalancing – `rebalance.html`

Displays current allocation versus recommended allocation and provides a rebalancing recommendation.

---

## 🎨 CSS

All frontend styling is contained in:

```text
css/style.css
```

The stylesheet provides:

* Dashboard layout
* Sidebar
* Navigation
* Cards
* Tables
* Buttons
* Forms
* Charts
* Risk indicators
* Responsive mobile design

---

## ⚙️ JavaScript

### `app.js`

Handles:

* Login
* Logout
* Local session state

### `dashboard.js`

Handles:

* Portfolio allocation chart
* Dashboard visualization

### `optimization.js`

Handles:

* Optimization form
* Optimization interaction
* Future backend optimization API integration

### `risk.js`

Handles:

* Risk monitoring
* Risk thresholds
* Risk status

### `simulation.js`

Handles:

* Market shock selection
* Simulation results
* Risk response

### `rebalance.js`

Handles:

* Rebalancing recommendation
* Rebalancing interaction

---

## 🔐 Demo Login

For the current frontend prototype:

```text
Username: admin
Password: admin
```

These credentials are only for the hackathon prototype.

---

## ▶️ How to Run

### Step 1

Open the project in VS Code:

```text
INIT26-CODEX
```

### Step 2

Open:

```text
frontend/index.html
```

### Step 3

Right-click `index.html`.

Select:

```text
Open with Live Server
```

### Step 4

The CapitalGuard login page will open in the browser.

Use:

```text
Username: admin
Password: admin
```

---

## 📱 Mobile Testing

The frontend is responsive and can be tested on a mobile device.

For local network testing, start Live Server and access the laptop's local IP address from the phone.

Example:

```text
http://192.168.1.100:5500/frontend/index.html
```

The exact IP address depends on the laptop's network.

---

## 🔗 Backend Integration

The frontend will connect to the Flask backend through REST APIs.

Expected endpoints:

```text
GET  /api/assets
GET  /api/portfolio
GET  /api/risk
POST /api/optimize
POST /api/simulate
POST /api/rebalance
```

Example frontend API request:

```javascript
fetch("http://localhost:5000/api/portfolio")
    .then(response => response.json())
    .then(data => {
        console.log(data);
    });
```

---

## 🔄 Frontend Data Flow

```text
User
  ↓
Frontend UI
  ↓
JavaScript
  ↓
Flask REST API
  ↓
Backend Logic
  ↓
Database
  ↓
Response
  ↓
Dashboard
```

---

## 👥 Frontend Team Responsibility

The frontend member is responsible for:

* UI/UX design
* HTML pages
* CSS styling
* JavaScript interactions
* Dashboard charts
* Risk visualization
* Simulation interface
* Rebalancing interface
* Backend API integration
* Mobile responsiveness

---

## 🚀 Future Improvements

* Real-time portfolio updates
* Live market data
* Interactive charts
* Advanced risk visualization
* Real-time alerts
* Authentication and authorization
* Improved mobile UI
* WebSocket-based live updates

---

## 🏆 Project

**CapitalGuard**

> Automated Asset & Capital Management, Risk Control and Portfolio Optimization Platform.

Developed as a FinTech hackathon project.
