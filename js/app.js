// ===============================
// CAPITALGUARD COMMON JAVASCRIPT
// ===============================

// INIT DB
function getUsers() {
    const users = localStorage.getItem("capitalguard_users");
    if (!users) {
        // Default admin user
        const defaultUsers = [{username: "admin", password: "admin"}];
        localStorage.setItem("capitalguard_users", JSON.stringify(defaultUsers));
        return defaultUsers;
    }
    return JSON.parse(users);
}

// Ensure DB exists on load
getUsers();


// TOGGLE VIEWS
function toggleView(view) {
    const loginView = document.getElementById("loginView");
    const registerView = document.getElementById("registerView");
    if (!loginView || !registerView) return;

    if (view === "register") {
        loginView.style.display = "none";
        registerView.style.display = "block";
    } else {
        registerView.style.display = "none";
        loginView.style.display = "block";
    }
}


// LOGIN
function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const message = document.getElementById("loginMessage");

    if (!username || !password) {
        message.textContent = "Please enter both username and password";
        message.style.color = "#d64545";
        return;
    }

    const users = getUsers();
    const user = users.find(u => u.username === username && u.password === password);

    if (user) {
        localStorage.setItem("capitalguard_logged_in", "true");
        window.location.href = "dashboard.html";
    } else {
        message.textContent = "Invalid username or password";
        message.style.color = "#d64545";
    }
}


// REGISTER
function register() {
    const username = document.getElementById("regUsername").value.trim();
    const password = document.getElementById("regPassword").value.trim();
    const confirmPassword = document.getElementById("regConfirmPassword").value.trim();
    const message = document.getElementById("registerMessage");

    if (!username || !password || !confirmPassword) {
        message.textContent = "All fields are required";
        message.style.color = "#d64545";
        return;
    }

    if (password !== confirmPassword) {
        message.textContent = "Passwords do not match";
        message.style.color = "#d64545";
        return;
    }

    const users = getUsers();
    if (users.find(u => u.username === username)) {
        message.textContent = "Username already exists";
        message.style.color = "#d64545";
        return;
    }

    // Add user
    users.push({ username, password });
    localStorage.setItem("capitalguard_users", JSON.stringify(users));

    message.textContent = "Account created successfully! Logging in...";
    message.style.color = "#28a745"; // Green success color

    // Auto-login
    setTimeout(() => {
        localStorage.setItem("capitalguard_logged_in", "true");
        window.location.href = "dashboard.html";
    }, 1000);
}


// LOGOUT
function logout() {
    localStorage.removeItem("capitalguard_logged_in");
    window.location.href = "index.html";
}